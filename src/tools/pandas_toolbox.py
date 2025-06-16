from langchain.tools import tool
import pandas as pd

@tool
def read_df(path: str) -> pd.DataFrame:
    """
    Read csv file.

    Parameters
    ----------
    path : str
        Path to csv file.
    
    Returns:
        pd.DataFrame: Imported dataframe
    
    Example:
        >>> df = read_df.invoke({"path": "data/agent_experiments/summary.csv"}) 
        >>> df.shape
        '(20, 5)'
    """
    
    if not path.endswith(".csv"):
        return ValueError(f"{path} is not a valid .csv file")
    return pd.read_csv(path)

@tool
def query_df(df, query: str):
    """
    Query DataFrame. Uses pandas.DataFrame.query built-in method.

    Parameters
    ----------
    df 
        Data Frame Object
    query: str
        Expression
    
    Returns:
        Queried data object
    
    Example:
        >>> queried_df = query_df.invoke({"df": df, "query": "accuracy > 0.1"})
        >>> queried_df.shape
        '(10, 5)'
    """
    
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        temp_data = df
        df = pd.DataFrame(temp_data)
        del temp_data
        
    return df.query(query)  # OPTIMIZE: to_markdown method + tabulate dependency


if __name__ == "__main__":
    print("Testing module...")
    print("Importing Data...")
    df = read_df.invoke({"path": "data/agent_experiments/summary.csv"})  
    print("-" * 40, "\nImported df:\n")
    print(df)

    queried_df = query_df.invoke({"df": df, "query": "accuracy > 0.1"})  
    print("-" * 40, "\nQueried df:\n")
    print(queried_df)