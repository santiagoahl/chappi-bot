from langchain.tools import tool
from tavily import TavilyClient
import os, dotenv

dotenv.load_dotenv()

search_engine = TavilyClient(api_key=os.getenv(key="TAVILY_API_KEY"))

@tool
def web_search(query: str, max_results: int = 4) -> str:
    """
    Run a web search to find information in the internet.

    Parameters
    ----------
    query : str
        Question to find out about
    max_results: int
        Top search results allowed

    Returns:
        str: First results of the search result

    Example:
        >>> web_search('Who is Luis Diaz')  # TODO: format this docstring
        'Luis Fernando Díaz Marulanda (born 13 January 1997) is a Colombian professional footballer who plays as a left winger or forward for Premier League club Liverpool and the Colombia national team.'
    """
    search_result_raw = search_engine.search(
        query, search_depth="advanced", max_results=max_results, include_answer=True
    )
    search_result = search_result_raw.get("answer", "No answers found.")
    return search_result

if __name__ == "__main__":
    user_query = input("Pass a topic / word to search for: ")
    search_result = web_search.invoke(input=user_query, max_results=2)
    print("Results")
    print("=" * 40)
    print(search_result)