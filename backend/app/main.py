from fastapi import FastAPI
from typing import Optional
from backend.services.agent_service import Agent

app = FastAPI()


@app.get("chappibot/query/prompt={prompt}")  # Q: How to pass a file?
def invoke_agent(
    prompt: Optional[str] = "hello ai",
) -> str:  # Q: How to pass a given prompt
    """
    Get the response from the agent.

    Parameters
    ----------
    prompt: Optional[str]

    Returns:
        str: AI Response

    Example:
        >>> invoke_agent('Who was Nicola Tesla')
        'Nikola Tesla was a Serbian-American engineer, futurist, and inventor. He is known for his contributions to the design of the modern AC electricity supply system.'
    """
    ai_assistant = Agent()
    return {
        "chappibot_response": ai_assistant.run(prompt)
    }  # Q: How to pass the statuscode? 
