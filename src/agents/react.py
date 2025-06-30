# Libraries
from langchain_core.tools.base import BaseTool
from langgraph.graph import START, END, StateGraph
from typing import TypedDict, List, Optional, Literal, Union
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
    ToolMessage,
)
from langchain_core.runnables.graph import MermaidDrawMethod
from langgraph.checkpoint.memory import MemorySaver

from asyncio import to_thread  # Asyncronous processing
from dotenv import load_dotenv
import os, sys
import aiofiles
import sys

# from langgraph.prebuilt import ToolNode, tools_condition

from langfuse.callback import CallbackHandler
from playwright.async_api import async_playwright
from langchain_community.agent_toolkits.playwright.toolkit import (
    PlayWrightBrowserToolkit,
)
import asyncio

tools_list = []
clean_browser = None
tools_by_name = {}
model_with_tools = None
_tools_initialized = False
_tools_lock = asyncio.Lock()

async def initialize_tools():
    global tools_list, clean_browser, tools_by_name, model_with_tools, _tools_initialized

    async with _tools_lock:  # Esto se libera automáticamente
        if _tools_initialized:
            print("Tools already initialized")
            return

        #print("Initializing tools")
        try:
            await import_local_modules()
            tools_list, clean_browser = await setup_tools()
            tools_by_name = {tool.name: tool for tool in tools_list}
            model_with_tools = model.bind_tools(tools_list)
            _tools_initialized = True
            print("Initialized tools")
        except Exception as e: 
            print(f"Error when initializing tools: {e}")
            raise 
 

async def import_local_modules() -> None:
    src_path = await asyncio.to_thread(lambda: os.path.abspath("src"))
    tools_path = await asyncio.to_thread(lambda: os.path.abspath("src/tools"))
    sys.path.append(src_path)
    sys.path.append(tools_path)


#asyncio.run(import_local_modules())  # DEPRECATED

sys.path.append(os.path.abspath("src"))
sys.path.append(os.path.abspath("src/tools"))

from tools import (
    calculator,
    search,
    code_executor,
    transcriber,
    post_processing,
    handle_text,
    pandas_toolbox,
    handle_json,
    chess_tool,
    handle_images,
)

# Load credentials
# var = "OPENAI_API_KEY"
# os.env[var] = os.getenv(var)
MAX_ITERATIONS = 7
ROOT_DIR = "/home/santiagoal/current-projects/chappie/"
AGENT_PROMPTS_DIR = os.path.join(ROOT_DIR, "prompts/agent/")
#SYS_MSG_PATH = os.path.join(AGENT_PROMPTS_DIR, "gaia_system_message.md")

load_dotenv()

use_studio = os.getenv("LANGGRAPH_STUDIO", "true").lower() == "true"  # BUG
# LLM Model


async def set_sys_msg(prompt_path: str):
    sys_msg = ""
    async with aiofiles.open(prompt_path, "r") as f:
        async for line in f:
            sys_msg += line
    return sys_msg


#SYSTEM_MESSAGE = asyncio.run(set_sys_msg(prompt_path=SYS_MSG_PATH))

model = ChatOpenAI(model="gpt-4o", temperature=0.5, max_retries=3, timeout=15)
langfuse_callback_handler = CallbackHandler()


# Define tools to use
async def setup_tools():
    # Cargar herramientas locales
    old_tools = [
        calculator.sum_,
        calculator.subtract,
        calculator.multiply,
        calculator.divide,
        search.web_search,
        search.pull_youtube_video,
        #search.fetch_online_pdf,
        code_executor.code_executor,
        transcriber.transcriber,
        post_processing.sort_items_and_format,
        handle_text.handle_text,
        pandas_toolbox.read_df,
        pandas_toolbox.query_df,
        handle_json.handle_json,
        chess_tool.grab_board_view,
        chess_tool.extract_fen_position,
        chess_tool.predict_next_best_move,
        handle_images.detect_objects,
    ]

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    async def cleanup_browser():
        await browser.close()
        await playwright.stop()

    # Herramientas del navegador
    web_toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    web_tools = web_toolkit.get_tools()
    # Optional: ajusta el timeout predeterminado de las tools Playwright
    for tool in web_tools:
        if hasattr(tool, "timeout"):
            tool.timeout = 60000 


    all_tools = old_tools + web_tools
    return all_tools, cleanup_browser



# tools_list, clean_browser = asyncio.run(setup_tools())  # DEPRECATED
# ToolNode(tools=tools_list, name="tools", )
#model_with_tools = model.bind_tools(tools_list)  # DEPRECATED


# State
class TaskState(TypedDict):
    messages: List[BaseMessage]
    iteration: Optional[int]


# tools_by_name = {tool.name: tool for tool in tools}
# tools_by_name = {tool.name: tool for tool in tools_list}  # Q: Does it work? # DEPRECATED


# Nodes
async def prepare_agent(state: TaskState) -> dict[str, list]:
    try:
        await initialize_tools()
    except Exception as e:
        print(f"Error initializing tools: {e}")
        raise

    messages = state.get("messages", [])
    if not any(isinstance(m, SystemMessage) for m in messages):
        sys_msg_path = os.path.join(AGENT_PROMPTS_DIR, "gaia_system_message.md")
        sys_msg = await set_sys_msg(prompt_path=sys_msg_path)
        messages.insert(0, SystemMessage(content=sys_msg))

    return {"messages": messages, "iteration": 0}



async def tools_node(state: TaskState) -> dict[str, list]:
    # result = []  # This line has been deleted cause we need to take in account chat history
    result = state.get("messages", [])
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = await tool.ainvoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


async def agent(state: TaskState) -> dict:
    """
    Agent node, contains the LLM Model used to process user requests.

    Parameters
    ----------
    state : TaskState
        Information history, which flows through the agent graph

    Returns:
        dict: State update

    Example:
        >>> from langchain_core.messages import HumanMessage
        >>> state = {"messages": [HumanMessage(content="What is LangGraph?")]}
        >>> output = agent(state)
        >>> isinstance(output["messages"][-1].content, str)
        True
    """

    # python
    chat_history = state.get("messages", [])
    iterations = state.get("iteration", 0)

    model_response = await model_with_tools.ainvoke(input=chat_history)

    # Ensure the response is valid before appending
    if isinstance(model_response, AIMessage):
        if model_response.tool_calls:
            iterations += 1
        chat_history.append(model_response)
    else:
        raise ValueError("Invalid model response format")

    state_update = {"messages": chat_history, "iteration": iterations}
    return state_update

    # chat_history = state.get("messages", [])
    # formatted_messages = [
    #    {
    #        "type": "human" if isinstance(msg, HumanMessage) else "ai",
    #        "content": msg.content,
    #    }

    #    for msg in chat_history
    # ]
    #
    ##formatted_messages = [
    ##    SystemMessage(content="You are a helpful assistant.")
    ##] + formatted_messages
    # formatted_messages = messages_from_dict(formatted_messages)
    # response = model_with_tools.invoke(formatted_messages)
    # current_iterations = state.get("iteration", 0)
    # chat_history.append(response)

    ## Handle tool calls if they exist
    # if hasattr(response, "tool_calls") and response.tool_calls:
    #    # This will trigger the tool execution in LangGraph
    #    return {
    #        "messages": chat_history + [response],
    #        "iteration": current_iterations + 1,
    #    }

    ## last_message = chat_history[-1]

    ## if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
    ##    print(last_message.tool_calls)

    # output = {"messages": chat_history}
    # return output


# Conditional Edges
def should_use_tool(state: TaskState) -> Literal["tools", END]:
    """
    Decides if using a tool is necessary to accomplish the task.

    Looks for the last Chat message, if it is a tool call, redirects the state to the Tool Node. The state is rooted to end otherwise.

    Parameters
    ----------
    state : TaskState
            Information history, which flows through the agent graph

    Returns:
        Literal["tools", END]: Next graph node to where the process should flow

    Example:
        >>> ('arg1', 'arg2')
        'output'
    """

    chat_history = state.get("messages", [])
    last_message = chat_history[-1]
    current_iterations = state.get("iteration", 0)

    if current_iterations > MAX_ITERATIONS:
        return END
    elif isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END


# Build Graph
memory = MemorySaver()  # Add persistence
builder = StateGraph(state_schema=TaskState)

builder.add_node("prepare_agent", prepare_agent)
builder.add_node("agent", agent)
builder.add_node("tools", tools_node)

builder.add_edge(START, "prepare_agent")
builder.add_edge("prepare_agent", "agent")
builder.add_conditional_edges(
    source="agent", path=should_use_tool, path_map=["tools", END]
)
builder.add_edge("tools", "agent")
# builder.add_edge("agent", END)

# memory = MemorySaver()
graph = builder.compile() if use_studio else builder.compile(checkpointer=memory)

# Save graph
# graph_json = graph.to_json()
# with open("../../langgraph.json", "w") as f:
#    f.write(graph_json)


# Save graph image
async def save_agent_architecture() -> None:
    # TODO: the new images path is /home/santiagoal/current-projects/chappie/data/images
    graph_image_bytes = await to_thread(lambda: graph.get_graph().draw_mermaid_png())
    with open("./images/agent_architecture.png", "wb") as f:
        f.write(graph_image_bytes)


# Test app
async def test_app() -> None:
    """
    Test the Agent behavior, including complete conversation thread
    """
    print("Testing App... \n")
    query = str(input("Ingresa tu pregunta: "))
    response = await graph.ainvoke(
        input={"messages": [HumanMessage(content=query)]},
        config={
            "callbacks": [langfuse_callback_handler],
            "configurable": {"thread_id": "1"},
        },
    )

    # Show chat history
    for msg in response["messages"]:
        role = msg.type
        content = msg.content
        print(f"{role.upper()}: {content}\n")
    return None


async def run_agent(
    user_query: str = None,
    print_response: bool = False,
    clean_browser_fn=None,
) -> Union[str, float, int]:
    try:
        query = user_query if user_query else input("Pass your question: ")
        agent_response = await graph.ainvoke(
            input={"messages": [HumanMessage(content=query)]},
            config={
                "callbacks": [langfuse_callback_handler],
                "configurable": {"thread_id": "1"},
            },
        )
        ai_answer = agent_response.get("messages", [])[-1].content
        if print_response:
            print(ai_answer)
        return ai_answer
    finally:
        if clean_browser_fn:
            await clean_browser_fn()


# DEBUG
user_query_debug = """
How many studio albums were published by Mercedes Sosa between 2000 and 2009 (included)? You can use the latest 2022 version of english wikipedia.
"""


if __name__ == "__main__":
    if "dev" not in sys.argv:
        agent_response = asyncio.run(
                run_agent( 
                    user_query=user_query_debug, 
                    print_response=True, 
                    clean_browser_fn=clean_browser
                )
        ) # DEBUG
        print(agent_response)

# TODO: Use a Local class for general path management
# TODO: Modularize script