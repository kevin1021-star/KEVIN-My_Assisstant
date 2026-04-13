import subprocess
import os
from langchain.tools import tool

@tool
def run_shell_command(command: str) -> str:
    """Executes a shell command (PowerShell) on the computer. Useful for coding, hacking, or system management. Be CAREFUL!"""
    try:
        # Running via powershell for more flexibility on Windows
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=30)
        output = result.stdout if result.stdout else result.stderr
        if not output:
             output = "Command executed successfully (no output)."
        return f"Shell Output:\n{output}"
    except Exception as e:
        return f"Shell Error: {str(e)}"

@tool
def read_code_file(file_path: str) -> str:
    """Reads the content of a file. Essential for helping AS with her assignments or coding projects."""
    try:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"Content of {file_path}:\n\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def write_code_file(file_path: str, content: str) -> str:
    """Writes content to a file. Used to help AS build software, complete college work, or create scripts."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True) if os.path.dirname(file_path) else None
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully written to {file_path}."
    except Exception as e:
        return f"Error writing file: {str(e)}"
