import ctypes
import sys

class Privileges:
    def __init__(self):
        # It is not needed
        pass

    @staticmethod
    def check_admin_rights():
        if ctypes.windll.shell32.IsUserAnAdmin():
            print("Current permissions: Administrator")
        else:
            print("Current permissions: Standard User")

    @staticmethod
    def run_as_admin():
        if ctypes.windll.shell32.IsUserAnAdmin():
            print("Current permissions: Administrator")
            return

        print("Requesting elevated permissions...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()