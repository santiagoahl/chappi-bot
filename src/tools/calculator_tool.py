from typing import Union

def sum_(a: Union[float, int], b: Union[float, int]) -> float:   
    """
    Runs a sum between a and b.

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

def subtract(a: Union[float, int], b: Union[float, int]) -> float:   
    """
    Runs a subtract between a and b.

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

def multiply(a: Union[float, int], b: Union[float, int]) -> float:   
    """
    Runs a multiply between a and b.

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

def divide(a: Union[float, int], b: Union[float, int]) -> float:   
    """
    Runs a divide between a and b.

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
    return a / b


if __name__=="__main__":
    a = float(input("Pass a: "))
    b = float(input("Pass b: "))
    
    print(sum_(a, b))