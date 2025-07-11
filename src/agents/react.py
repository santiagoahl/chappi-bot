# Libraries
from langchain_core.tools.base import BaseTool
from langchain_core.prompts import PromptTemplate
from langgraph.graph import START, END, StateGraph
from typing import TypedDict, List, Optional, Literal, Union
from langchain_openai import ChatOpenAI
import logging

# from cv2 import cv2
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
import time
import sys

# from langgraph.prebuilt import ToolNode, tools_condition

from langfuse.callback import CallbackHandler
from playwright.async_api import async_playwright
from langchain_community.agent_toolkits.playwright.toolkit import (
    PlayWrightBrowserToolkit,
)
import asyncio

logs_mode = False
debug_mode = False
save_agent_architecture = True

# Set up logger and debugger

logger = logging.getLogger(name="react")  # Initialize logger
logger.handlers.clear()  # Remove existing handlers
logger.setLevel(level=logging.INFO)  # Level of observability

debugger = logging.getLogger(name="react debugger")  # Initialize debugger
debugger.handlers.clear()  # Remove existing handlers
debugger.setLevel(level=logging.DEBUG)  # Level of observability

## Set logs handling
logs_handler = logging.StreamHandler()
logs_handler.setLevel(level=logging.INFO)

debug_handler = logging.StreamHandler()
debug_handler.setLevel(level=logging.DEBUG)

## Set logs formatter
logs_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(fmt=logs_format)
logs_handler.setFormatter(fmt=formatter)
debug_handler.setFormatter(fmt=formatter)

## Integrate handler
logger.addHandler(hdlr=logs_handler)
debugger.addHandler(hdlr=debug_handler)

# Prevent logs inherited filtering
logger.propagate = False
debugger.propagate = False

if logs_mode:
    logger.info("Preparing basic config...")

tools_list = []
clean_browser = None
tools_by_name = {}
model_with_tools = None
_tools_initialized = False
_tools_lock = asyncio.Lock()


async def initialize_tools():
    if logs_mode:
        logger.info("Initializing tool box...")
    global tools_list, clean_browser, tools_by_name, model_with_tools, _tools_initialized

    async with _tools_lock:  # Esto se libera automáticamente
        if _tools_initialized and logs_mode:
            logger.info("Tools already initialized")
            return

        # print("Initializing tools")
        try:
            await import_local_modules()
            tools_list, clean_browser = await setup_tools()
            tools_by_name = {tool.name: tool for tool in tools_list}
            model_with_tools = model.bind_tools(tools_list)
            _tools_initialized = True
            if logs_mode:
                logger.info("Tools successfully initialized")
        except Exception as e:
            print(f"Error when initializing tools: {e}")
            raise


async def import_local_modules() -> None:
    if logs_mode:
        logger.info("Setting up local modules...")
    src_path = await asyncio.to_thread(lambda: os.path.abspath("src"))
    tools_path = await asyncio.to_thread(lambda: os.path.abspath("src/tools"))
    sys.path.append(src_path)
    sys.path.append(tools_path)


# asyncio.run(import_local_modules())  # DEPRECATED

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
MAX_ITERATIONS = 7  # Max agent node - tool node attempts
ROOT_DIR = "/home/santiagoal/current-projects/chappie/"
AGENT_PROMPTS_DIR = os.path.join(ROOT_DIR, "prompts/agent/")
# SYS_MSG_PATH = os.path.join(AGENT_PROMPTS_DIR, "gaia_system_message.md")

if logs_mode:
    logger.info("Setting up environment variables...")
load_dotenv()

use_studio = os.getenv("LANGGRAPH_STUDIO", "true").lower() == "true"  # BUG
# LLM Model


async def set_sys_msg(prompt_path: str):
    sys_msg = ""
    async with aiofiles.open(prompt_path, "r") as f:
        async for line in f:
            sys_msg += line
    return sys_msg


# SYSTEM_MESSAGE = asyncio.run(set_sys_msg(prompt_path=SYS_MSG_PATH))

if logs_mode:
    logger.info("Preparing AI model...")
model = ChatOpenAI(model="gpt-4o", temperature=0.5, max_retries=3, timeout=15)
langfuse_callback_handler = CallbackHandler()


# Define tools to use
async def setup_tools():
    if logs_mode:
        logger.info("Setting up tools...")
    # Cargar herramientas locales
    old_tools = [
        calculator.sum_,
        calculator.subtract,
        calculator.multiply,
        calculator.divide,
        search.web_search,
        search.pull_youtube_video,
        # search.fetch_online_pdf,
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
# model_with_tools = model.bind_tools(tools_list)  # DEPRECATED


# State
class TaskState(TypedDict):
    messages: List[BaseMessage]
    iteration: Optional[int]


# tools_by_name = {tool.name: tool for tool in tools}
# tools_by_name = {tool.name: tool for tool in tools_list}  # Q: Does it work? # DEPRECATED


# Nodes
async def prepare_agent(state: TaskState) -> dict[str, list]:

    if debug_mode:
        debugger.debug("Preparing agent")
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
    if debug_mode:
        debugger.debug("Running tools node")
    # result = []  # This line has been deleted cause we need to take in account chat history
    result = state.get("messages", [])
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = await tool.ainvoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


async def agent_node(state: TaskState) -> dict:
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
    if debug_mode:
        debugger.debug("Running Agent Node...")

    # Get list of historical messages
    chat_history = state.get("messages", [])
    iterations = state.get("iteration", 0)

    if debug_mode:
        chat_history_msgs = [
            f"{raw_msg.type}: {raw_msg.content}\ntool_calls: {raw_msg.tool_calls if raw_msg.type=='ai' else 'None'}"
            for raw_msg in chat_history
        ]
        chat_history_msgs = "\n".join(chat_history_msgs).strip()
        debugger.debug(f"Passing input prompt...")
        time.sleep(2)
        debugger.debug(
            f"\n{chat_history_msgs}"
        )  # Q: Is using multiple ifs as here a bad practice
        debugger.debug(f"The AI Model is running...")

    model_response = await model_with_tools.ainvoke(input=chat_history)

    if debug_mode:
        time.sleep(3)
        debugger.debug(
            f"Query completed.\n\n{model_response.type}: {model_response.content}\n"
        )

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


async def double_check_node(
    state: TaskState,
) -> dict:  # Q: Can I save tokens by passing just the format_msg + last ai response
    """
    Check the AI final message and correct / fix if it is required.

    This is useful when the AI's output does not match the required format, in spite of the semantic correctness of it.

    Parameters
    ----------
    state: TaskState

    Returns:
        dict: State update with channels 'messages' and 'iteration'

    Example:
        >>> double_check_node({
            "messages": [AIMessage("The answer is twenty four")],
            "iteration": 1
           })
           '{
            "messages": [
                    AIMessage("The answer is twenty four"),
                    AIMessage("24"),
                ],
            "iteration": 1
           }'
    """


    # Get Sys msg
    sys_msg_path = os.path.join(AGENT_PROMPTS_DIR, "gaia_system_message.md")
    sys_msg = ""
    with open(sys_msg_path, "r") as f:
        for line in f:
            sys_msg += line

    # Gather chat history
    chat_history = state.get("messages", [])
    iteration = state.get("iteration", 0)

    #  Get original user query and AI response
    user_query_msg = next(filter(lambda message: message.type == "human", chat_history))
    user_query = user_query_msg.content

    ai_response_msg = chat_history[-1]
    ai_message = ai_response_msg.content

    # Debug if necessary
    if debug_mode:
        debugger.debug("Verifying response...")
        chat_history_msgs = [
            f"{raw_msg.type}: {raw_msg.content}\ntool_calls: {raw_msg.tool_calls if raw_msg.type=='ai' else 'None'}"
            for raw_msg in chat_history
        ]
        chat_history_msgs = "\n".join(chat_history_msgs).strip()
        debugger.debug(f"Passing input prompt...")
        time.sleep(2)
        debugger.debug(
            f"\n{chat_history_msgs}"
        )  # Q: Is using multiple ifs as here a bad practice

    #  Read the instructions to pass to the agent
    request_to_format_path = os.path.join(
        AGENT_PROMPTS_DIR, "format_reponse_system_message.md"
    )
    instructions = ""
    with open(request_to_format_path, "r") as f:
        for line in f:
            instructions += line

    # Prepare input to format
    prompt_to_format = PromptTemplate.from_template(
        """# Context:\n{sys_message}# Instructions to double check:\n{instructions}\n\n# Original User Request:\n{usr_query} \n\n# AI message to format: {ai_message_raw}"""
    )
    prompt_value = prompt_to_format.invoke(
        {
            "sys_message": "",  # temp#"sys_msg",
            "instructions": instructions,
            "usr_query": user_query,
            "ai_message_raw": ai_message,
        }
    )
    formatted_request = SystemMessage(content=prompt_value.to_string())
    # Ask AI for formatting
    ai_msg_formated = await model_with_tools.ainvoke(input=[formatted_request])

    # Save results
    chat_history.append(ai_msg_formated)
    state_update = {
        "messages": chat_history,
        "iteration": iteration,
    }
    if debug_mode:
        debugger.debug(f"AI response verified\n\nai: ai:{ai_msg_formated.content}")
    return state_update


# Conditional Edges
def should_use_tool(state: TaskState) -> Literal["tools", "double_check"]:
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
        return "double_check"
    elif isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "double_check"


if logs_mode:
    logger.info("Preparing Agent...")
# Build Graph
memory = MemorySaver()  # Add persistence
builder = StateGraph(state_schema=TaskState)

builder.add_node("prepare_agent", prepare_agent)
builder.add_node("agent", agent_node)
builder.add_node("tools", tools_node)
builder.add_node("double_check", double_check_node)  # Fix AI response

builder.add_edge(START, "prepare_agent")
builder.add_edge("prepare_agent", "agent")
builder.add_conditional_edges(
    source="agent", path=should_use_tool, path_map=["tools", "double_check"]
)
builder.add_edge("tools", "agent")
# builder.add_edge("agent", "double_check")
builder.add_edge("double_check", END)

# memory = MemorySaver()
graph = builder.compile() if use_studio else builder.compile(checkpointer=memory)

# Save graph

# graph_json = graph.to_json()
# with open("../../langgraph.json", "w") as f:
#    f.write(graph_json)

if save_agent_architecture:
    graph_image_bytes = graph.get_graph().draw_mermaid_png()
    with open("data/images/agent_architecture.png", "wb") as f:
        f.write(graph_image_bytes)

# Save graph image
# sync def save_agent_architecture() -> None:
#   # TODO: the new images path is /home/santiagoal/current-projects/chappie/data/images
#   graph_image_bytes = await to_thread(lambda: graph.get_graph().draw_mermaid_png())
#   with open("data/images/agent_architecture.png", "wb") as f:
#       f.write(graph_image_bytes)


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
        if logs_mode:
            logger.info("Agent task succesfully completed.")
        if print_response:
            print(ai_answer)
        return ai_answer
    finally:
        if clean_browser_fn:
            await clean_browser_fn()



# DEBUG OVER DEBUG
# user_query_debug = "HI"
if __name__ == "__main__":
    # DEBUG
    user_query_debug = """
    I'm making a grocery list for my mom, but she's a professor of botany and she's a real stickler when it comes to categorizing things. I need to add different foods to different categories on the grocery list, but if I make a mistake, she won't buy anything inserted in the wrong category. Here's the list I have so far:

    milk, eggs, flour, whole bean coffee, Oreos, sweet potatoes, fresh basil, plums, green beans, rice, corn, bell pepper, whole allspice, acorns, broccoli, celery, zucchini, lettuce, peanuts

    I need to make headings for the fruits and vegetables. Could you please create a list of just the vegetables from my list? If you could do that, then I can figure out how to categorize the rest of the list into the appropriate categories. But remember that my mom is a real stickler, so make sure that no botanical fruits end up on the vegetable list, or she won't get them when she's at the store. Please alphabetize the list of vegetables, and place each item in a comma separated list.
    """
    if "dev" not in sys.argv:
        # Q: Can I visualize the event loop and parallel tasks?
        agent_response = asyncio.run(
            run_agent(
                user_query=user_query_debug,
                print_response=True,
                clean_browser_fn=clean_browser,
            )
        )  # DEBUG
        # print(agent_response)

# TODO: Use a Local class for general path management
# TODO: Modularize script
