import subprocess


def run_cmd_command_realtime(command):
    try:
        # Open a subprocess with pipes for stdout and stderr
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            text=True,
            bufsize=1,  # Line-buffered
            universal_newlines=True  # Use universal newlines
        )

        # Read and print the output line by line in real-time
        for line in process.stdout:
            print(line.strip())

        # Wait for the subprocess to finish
        process.wait()

        # Check the return code
        if process.returncode == 0:
            print("Command executed successfully.")
        else:
            print(f"Command failed with return code {process.returncode}")

    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {str(e)}")


def run_cmd_command(command):
    import subprocess
    commands_separated = command.splitlines()
    try:
        results = []
        for command in commands_separated:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            results.append(result.stdout.strip())
        output_string = '\n'.join(results)
        return output_string
    except subprocess.CalledProcessError as e:
        print(f"Command execution failed with error: {e}")
        return None
