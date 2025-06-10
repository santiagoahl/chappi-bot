from langchain.tools import tool


@tool
def handle_text(file_path: str) -> str:  # Q: How to validate file endswith txt?
    """
    Process text files.

    This tool receives a file path as input and returns a string object containing the text object.
    For extensions different from .txt, for .docx files, check the tool handle_office_documents()

    Args:
        file_path (str): Path to text file. It must have extension .txt

    Returns:
        str: Processed text object

    Raises:
        ValueError: In such a case the file_path points to a non .txt file

    Example:
        >>> path = "~/santiagoal/current-projects/chappie/data/temp-data/temp_text.txt"
        >>> handlle_text(path)
        Hi, this is a sample text \n
        that's all:
    """
    filetype = file_path.split(".")[-1]
    try:
        assert file_path.endswith(filetype)
    except AssertionError:
        raise ValueError(
            f"{file_path} has no valid file type. Received .{filetype}, expected .txt"
        )

    with open(file_path, "r") as text_file:
        text = text_file.read()

    return text


if __name__ == "__main__":
    print("Testing process...\n", "-" * 50, "\n")
    print("Processing text...\n", "-" * 50, "\n")
    path = "data/temp-data/temp_text.txt"
    text = handle_text.invoke({'file_path': path})
    print("The text has been processed...\n", "-" * 50, "\n")
    print(text)

# TODO: implement pydantic to validate data
