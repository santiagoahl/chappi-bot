# TODO: Use a Local class for general path management

# This MVP includes no tools even though these are imported

# Libraries
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

# from langgraph.prebuilt import ToolNode, tools_condition

from langfuse.callback import CallbackHandler


sys.path.append(os.path.abspath("src"))
# sys.path.append(os.path.abspath("src/tools"))
from tools import calculator, search, code_executor

# Load credentials
# var = "OPENAI_API_KEY"
# os.env[var] = os.getenv(var)
MAX_ITERATIONS = 7
ROOT_DIR = "/home/santi/current-projects/chappie/"
AGENT_PROMPTS_DIR = os.path.join(ROOT_DIR, "prompts/agent/")

load_dotenv()

use_studio = os.getenv("LANGGRAPH_STUDIO", "false").lower() == "true"
# LLM Model

SYSTEM_MESSAGE = ""
with open(os.path.join(AGENT_PROMPTS_DIR, "gaia_system_message.md"), "r") as f:
    for line in f:
        SYSTEM_MESSAGE += line

model = ChatOpenAI(model="gpt-4o", temperature=0.0)
langfuse_callback_handler = CallbackHandler()

# TODO: define the tools list smarter (e.g. using **)
tools_list = [
    calculator.sum_,
    calculator.subtract,
    calculator.multiply,
    calculator.divide,
    search.web_search,
    code_executor.code_executor
]

# ToolNode(tools=tools_list, name="tools", )
model_with_tools = model.bind_tools(tools_list)


# State
class TaskState(TypedDict):
    messages: List[BaseMessage]
    iteration: Optional[int]


# tools_by_name = {tool.name: tool for tool in tools}
tools_by_name = {tool.name: tool for tool in tools_list}  # Q: Does it work?


# Nodes
def prepare_agent(state: TaskState) -> dict[str, list]:
    "Agent Start Node, responsible to define Agent behavior"
    messages = state.get("messages", [])

    if not any(isinstance(m, SystemMessage) for m in messages):
        messages.insert(0, SystemMessage(content=SYSTEM_MESSAGE))

    return {"messages": messages, "iteration": 0}


def tools_node(state: TaskState) -> dict[str, list]:
    # result = []  # This line has been deleted cause we need to take in account chat history
    result = state.get("messages", [])
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


def agent(state: TaskState) -> dict:
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

    model_response = model_with_tools.invoke(input=chat_history)

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
# TODO: the new images path is /home/santi/current-projects/chappie/data/images
    graph_image_bytes = await to_thread(lambda: graph.get_graph().draw_mermaid_png())
    with open("./images/agent_architecture.png", "wb") as f:
        f.write(graph_image_bytes)



# Test app
def test_app() -> None:
    """
    Test the Agent behavior, including complete conversation thread
    """
    print("Testing App... \n")
    query = str(input("Ingresa tu pregunta: "))
    response = graph.invoke(
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

def run_app(user_query: str = None, print_response: bool = False) -> Union[str, float, int]:
    """
    Call the agent, developing it for GAIA benchmark questions.

    Returns:
        Union[str, float, int]: AI Answer

    Example:
        >>> import react  # Ensure to include this module to sys path
        >>> react.run()
        >>> Pass your question:
        >>> Calculate the result of: (12 multiplied by 3) minus (15 divided by 5) plus (8 added to 2)
        '43.0'
    """
    
    query = user_query if user_query else input("Pass your question: ")
    response = graph.invoke(
        input={"messages": [HumanMessage(content=query)]},
        config={
            "callbacks": [langfuse_callback_handler],
            "configurable": {"thread_id": "1"},
        },
    )
    ai_answer = response.get("messages", [])[-1].content
    
    if print_response:
        print(ai_answer)
        
    return ai_answer


if __name__ == "__main__":
    run_app(print_response=True)