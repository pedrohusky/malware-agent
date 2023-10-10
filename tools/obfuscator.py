import base64
import os
import time
from alive_progress import alive_bar


class Obfuscator:
    def __init__(self):
        # It is not needed to create variables
        pass

    @staticmethod
    def code(file):
        print(file)
        with open(file, 'r', encoding="utf-8") as f:
            code = f.read()
        return code

    @staticmethod
    def separate_imports(file):
        imports = []
        with open(file, "r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f]
            for line in lines:
                if line.startswith("import") or line.startswith("from"):
                    imports.append(line)
        return imports

    @staticmethod
    def obfuscate(code, level):
        obfuscated = f"\nexec(base64.a85decode({base64.a85encode(code.encode('utf-8', errors='strict'))}))"
        with alive_bar(level) as bar:
            for _ in range(level):
                obfuscated = f"import base64\nexec(base64.a85decode({base64.a85encode(obfuscated.encode('utf-8', errors='strict'))}))"
                bar()
        return obfuscated

    @staticmethod
    def save(obfuscated, file, imports=None):
        if not os.path.exists('obfuscated'):
            os.makedirs('obfuscated')
        with open(f"obfuscated/{file.replace('.py', '')}-obfuscated.py", 'a', encoding="utf-8") as f:
            if imports:
                for module in imports:
                    f.write(module + "\n")
            f.write(obfuscated)

    @staticmethod
    def clean(file):
        obfuscated_file = f"{file.replace('.py', '')}-obfuscated.py"
        if os.path.exists(obfuscated_file):
            os.remove(obfuscated_file)

    def obfuscate_file(self, filename, level):
        file = f"{filename}"
        self.clean(file)
        time.sleep(0.5)
        code_content = self.code(file)
        imports = self.separate_imports(file)
        obfuscated_code = self.obfuscate(code_content, level)
        # Call the obfuscate function
        file_name = os.path.basename(file)
        clean_directory = (file
                           .replace(os.getcwd(), "")
                           .replace(file_name, "")
                           .replace("C:\\", "")
                           .strip())
        if clean_directory == "\\":
            clean_directory = ""
        self.save(obfuscated_code, clean_directory + file_name, imports)
