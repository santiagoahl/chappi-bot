from langchain_core.tools import tool

@tool
def sort_items_and_format(items: list[str]) -> str:
    """
    Alphabetize a set of words.

    Parameters
    ----------
    items : list
        Words to bet sorted
    
    Returns:
        str: Alphabetized and formated text
    """
    sorted_items = sorted(items, key=lambda x: x.split()[0].lower())
    return ", ".join(sorted_items)
