from typing import Literal
from langchain.tools import tool
import subprocess


def read_multiline_code() -> Literal:
    print("Write your python code. End input with an empty line.")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines)


@tool
def code_executor(src_code: str) -> str:
    """
    Tool to let the Agent run its own python code.

    Parameters
    ----------
    src_code : str
        Code to be executed. Must have multilines and indentation spaces,
        in general, respect the python code syntax

    Returns:
        str: code result

    Example:
        >>> code_executor.invoke(input="print('hello world!')")
        'hello world!'
    """
    try:
        result = subprocess.run(
            ["python", "-c", src_code], capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip() or "Code Executed with no output."
    except Exception as e:
        return f"Execution failed: {str(e)}"


if __name__ == "__main__":
    # TODO: include multiline function to run code in the terminal
    code = input("Write your python code " + "\n" + ("=" * 20) + "\n")
    output = code_executor.invoke(input=code)
    print(output)