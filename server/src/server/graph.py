import operator
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

all_tools = {
    "add": lambda a, b: a + b,
    "subtract": lambda a, b: a - b,
    "multiply": lambda a, b: a * b,
    "divide": lambda a, b: a / b,
}


class State(TypedDict):

    # events is a list of events received from the model
    events: list

    # tools is the list of tools the model should have access to
    # when it is updated, we send an update session event to the api
    tools: list[str]

    # instructions is the model instructions to help steer the conversation
    instructions: str

    # tool_calls is the list of calls to the tools that the model has requested
    # tool_results is the list of results from the tools
    # annotated with update method
    tool_calls_and_results: Annotated[dict, operator.or_]


def start(state: State) -> State:
    return state


def execute_tools(state: State) -> State:
    result = {}
    for tool_call, tool_result in state["tool_calls_and_results"].items():
        if tool_result is None:
            # tool hasn't been called yet
        state["tool_results"].append(tool_call)
    for tool_call in state["tool_calls"]:
        state["tool_results"].append(tool_call)
    return result


graph_builder = StateGraph(State)

graph_builder.add_node(START, start)


# start node should be a noop
async def execute_tools(state: State) -> State:
    for tool_call in state["tool_calls"]:
        state["tool_results"].append(tool_call)
    return state


graph = graph_builder.compile()
