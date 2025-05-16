from typing import Union
from langchain.tools import tool


@tool
def sum_(a: Union[float, int], b: Union[float, int]) -> float:   
    """
    Computes the sum between a and b.

    Parameters
    ----------
    a : float | int
    b : float | int
    
    Returns:
        float: result of sum a with b
    
    Example:
        >>> sum_(3.0, 1.5)
        4.5
    """
    return a + b

@tool
def subtract(a: Union[float, int], b: Union[float, int]) -> float:   
    """
    Computes the subtract between a and b.

    Parameters
    ----------
    a : float | int
    b : float | int
    
    Returns:
        float: result of subtract a with b
    
    Example:
        >>> subtract(3.0, 1.5)
        1.5
    """
    return a - b

@tool
def multiply(a: Union[float, int], b: Union[float, int]) -> float:   
    """
    Computes the multiply between a and b.

    Parameters
    ----------
    a : float | int
    b : float | int
    
    Returns:
        float: result of multiply a with b
    
    Example:
        >>> multiply(3.0, 1.5)
        4.5
    """
    return a * b

@tool
def divide(a: Union[float, int], b: Union[float, int]) -> float:   
    """
    Computes the divide between a and b.

    Parameters
    ----------
    a : float | int
    b : float | int
    
    Returns:
        float: result of divide a with b
    
    Example:
        >>> divide(3.0, 1.5)
        2.0
    """
    try:
        return a / b
    except:
        raise ValueError("Division By 0.0 not allowed")


if __name__=="__main__":
    a = float(input("Pass a: "))
    b = float(input("Pass b: "))
    
    print(sum_(a, b))