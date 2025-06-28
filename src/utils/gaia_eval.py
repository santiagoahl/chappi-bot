# Useful fucntions to validate performance of agents regarding GAIA dataset
import pandas as pd
from typing import Literal
import os
import time

os.sys.path.append("../agents")
import react
import gaia_scorer

def evaluate_response(row: pd.Series) -> Literal[0, 1]:
    """
    Evaluate Agent responses of GAIA-like answers. Exact match is mandatory for good responses

    Parameters
    ----------
    
    row: pd.Series
        Array containing fields 'Agent response' and 'Final answer'

    Returns:
        Literal[0, 1]: 0 if the answer is not correct, 1 otherwise

    Example:
        >>> results_df["is_correct"] = results_df.apply(func=eval_answer, axis=1)
    """
    model_res = row["Agent response"]
    gt_ans = row["Final answer"]
    score = gaia_scorer.question_scorer(
        model_answer=model_res, 
        ground_truth=gt_ans
    )
    score = int(score) 
    return score

def get_agent_response(row: pd.Series) -> str:
    """
    Map dataset questions to Responses using .apply pandas method.

    Parameters
    ----------
    row : pd.Series
        Series containing fields 'Question' and 'file_path' 
    agent
        Agent module with integrate function .run_app()

    Returns:
        str: Agent Response

    Example:
        >>> results_df["Agent response"] = results_df.apply(func=get_agent_response, axis=1)

    """
    time.sleep(5)  # Wait to avoid gpt-4o tokens-per-minute limit
    raw_user_query = row["Question"]
    attached_files = row["file_path"]
    user_query = f"User request:{raw_user_query}\nAttached files: {attached_files if attached_files is not None else 'None'}"
    print(f"attached_files: {attached_files}")

    agent_response = react.run_app(user_query=user_query)
    agent_response = str(agent_response)
    return agent_response
