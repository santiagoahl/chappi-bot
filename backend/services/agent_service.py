from src.agents.react import run_agent


class Agent():
    def __init__(self):
        self.user_query = None
        self.ai_response = None
        self.files = None

    def run(self, user_query: str) -> str:   
        """
        Get the response of the chappibot AI assistant 

        Parameters
        ----------
        user_query: str
            Request from the user

        Returns:
            str: AI agent response

        Example:
            >>> run('who was Mileva Maric?')
            'She was a Serbian physicist and mathematician'
        """
        self.user_query = user_query
        return run_agent(self.user_query)
