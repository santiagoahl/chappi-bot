# Useful fucntions to validate performance of agents regarding GAIA dataset
import pandas as pd
from typing import Literal
import os

os.sys.path.append("../agents")
import react


def eval_answer(row: pd.Series) -> Literal[0, 1]:
    """
    Evaluate Agent responses of GAIA-like answers. Exact match is mandatory for good responses

    Parameters
    ----------
    model_response: str
        Model response to the question
    gt_answer: str
        Ground truth answer to the question

    Returns:
        Literal[0, 1]: 0 if the answer is not correct, 1 otherwise

    Example:
        >>> results_df["is_correct"] = results_df.apply(func=eval_answer, axis=1)
    """
    model_response = row["Agent response"]
    gt_answer = row["Final answer"]
    return 1 if (model_response == gt_answer) else 0


def get_agent_response(row: pd.Series) -> str:
    """
    Map dataset questions to Responses using .apply pandas method.

    Parameters
    ----------
    row : pd.Series
        Series with with a field "Question"
    agent
        Agent module with integrate function .run_app()

    Returns:
        str: Agent Response

    Example:
        >>> results_df["Agent response"] = results_df.apply(func=get_agent_response, axis=1)

    """

    raw_user_query = row["Question"]
    attached_files = row["file_path"]
    user_query = f"User request:{raw_user_query}\nAttached files: {attached_files if attached_files is not None else 'None'}"

    agent_response = react.run_app(user_query=user_query)
    agent_response = str(agent_response)
    return agent_response
