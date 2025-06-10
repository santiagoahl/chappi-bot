from langchain.tools import tool
import json

@tool
def handle_json(file_path: str) -> str:  
    """
    Process json files.

    This tool receives a file path to a json file as input and returns a dict object containing the json object.

    Args:
        file_path (str): Path to json file. It must have extension .json

    Returns:
        dict: Processed json object

    Raises:
        ValueError: In such a case the file_path points to a non .json file

    Example:
        >>> path = "data/temp-data/temp_json.json"
        >>> handle_json(path)
        {'key1': 1, 'key2': 2, 'key3': 30}
    """
    filetype = file_path.split(".")[-1]
    try:
        assert file_path.endswith(filetype)
    except AssertionError:
        return ValueError(
            f"{file_path} has no valid file type. Received .{filetype}, expected .json"
        )
        
    with open(file_path, "r") as f:
        obj = f.read()

    return json.loads(obj)
    

if __name__ == "__main__":
    print("Testing process...\n", "-" * 50, "\n")
    print("Processing json...\n", "-" * 50, "\n")
    path = "data/temp-data/temp_json.json"
    result = handle_json.invoke({'file_path': path})
    print("The json has been processed...\n", "-" * 50, "\n")
    print(result)

# TODO: implement pydantic to validate data
