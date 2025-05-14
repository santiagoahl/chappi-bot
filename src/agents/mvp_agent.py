# This MVP includes no tools even though these are imported

# Libraries
from langgraph.graph import START, END, StateGraph
from typing import TypedDict, List, Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode
import os, sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath("src"))
# sys.path.append(os.path.abspath("src/tools"))
from tools import calculator_tool

# Load credentials
# var = "OPENAI_API_KEY"
# os.env[var] = os.getenv(var)

load_dotenv()

# LLM Model
model = ChatOpenAI(model="gpt-4o", temperature=0.0)
tool_list = [
    calculator_tool.sum_,
    calculator_tool.subtract,
    calculator_tool.multiply,
    calculator_tool.divide,
]
tool_node = ToolNode(tool_list)
model_with_tools = model.bind_tools(tool_list)


# State
class TaskState(TypedDict):
    messages: List


# Nodes
def agent_node(state: TaskState) -> dict:
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
            >>> output = agent_node(state)
            >>> isinstance(output["messages"][-1].content, str)
            True
    """
    
    chat_history = state.get("messages", [])
    response = model_with_tools.invoke(chat_history)
    new_history = chat_history + [response]
    output = {"messages": new_history}

    return output


# Conditional Edges
def should_use_tool(state: TaskState) -> Literal["tool_node", END]:   
    """
    Decides if using a tool is necessary to accomplish the task.
    
    Looks for the last Chat message, if it is a tool call, redirects the state to the Tool Node. The state is rooted to end otherwise.

    Parameters
    ----------
    state : TaskState
            Information history, which flows through the agent graph
    
    Returns:
        Literal["tools, END]: Next graph node to where the process should flow
    
    Example:
        >>> ('arg1', 'arg2')
        'output'
    """
    chat_history = state.get("chat_history", [])
    last_message = chat_history[-1]
    nex_node = "tool_node" if last_message.tool_calls else END
        
    return next_node

# Build Graph
graph = StateGraph(state_schema=TaskState)

graph.add_node("agent_node", agent_node)
graph.add_node("tool_node", tool_node)

graph.add_edge(START, "agent_node")
graph.add_edge("agent_node", END)

app = graph.compile()

def test_app() -> None:   
    """
    Test the Agent behavior
    """
    print("Testing App... \n")
    query = str(input("Ingresa tu pregunta: "))
    response = app.invoke({"messages": [HumanMessage(content=query)]})
    for msg in response["messages"]:
        role = msg.type
        content = msg.content
        print(f"{role.upper()}: {content}\n")
    return None


if __name__ == "__main__":
    test_app()
