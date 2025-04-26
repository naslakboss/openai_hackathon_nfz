import logging
import time
from typing import Annotated, AsyncGenerator, List, TypedDict

from dotenv import load_dotenv
from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


load_dotenv()

logger = logging.Logger(__name__)


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


@tool
def what_day_and_time_is_it():
    """Tells the agent what day of the week and time is it"""
    return time.strftime("%A %H:%M:%S", time.localtime())


class CustomBroAgent:
    def __init__(
        self,
        tools: List[BaseTool],
        llm: BaseChatModel = ChatOpenAI(model="gpt-4o-mini"),
    ) -> None:
        logger.info("Initializing LLMAgent")
        in_memory_store = MemorySaver()
        llm_with_tools = llm.bind_tools(tools)
        tool_node = ToolNode(tools=tools)

        def chatbot(state: State) -> State:
            system_prompt = SystemMessage(
                content="""
You are a voice-enabled AI assistant developed to help blind users navigate the internet.
Your primary goal is to provide a clear, high-level overview of a website’s structure and then, on request, guide users through detailed content or interactive elements.

You start with a open browser.
Greet the user with information about the page they are on.

How to guide the user:
- When you get the snapshot of the page, explain high level structure of the page.
- If you are exmplaining the whole page in general, keep it short to a 2/3 sentences.
- If the user asks about the specific part go into the details more.


About the output:
- Return all answers in the format that is ready to be spoken out loud. All the text will be processed by a text to speech algorithm.

"""
            )
            msgs = [system_prompt] + state["messages"]
            return {"messages": [llm_with_tools.invoke(msgs)]}

        graph_builder = StateGraph(State)
        graph_builder.add_node("chatbot", chatbot)  # type: ignore
        graph_builder.add_node("tools", tool_node)  # type: ignore

        graph_builder.add_conditional_edges(
            "chatbot",
            tools_condition,
        )
        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_edge("tools", "chatbot")
        graph_builder.add_edge("chatbot", END)

        self.graph: CompiledStateGraph = graph_builder.compile(
            checkpointer=in_memory_store,
        )  # type: ignore

    async def chat_astream(self, messages: List[BaseMessage], conversation_id: str) -> AsyncGenerator[BaseMessage, None]:
        async for event in self.graph.astream(  # type: ignore
            input={"messages": messages},
            config=self._get_configurable(conversation_id),
            stream_mode="messages",
        ):
            yield event[0]  # type: ignore

    def _get_configurable(self, conversation_id: str) -> RunnableConfig:
        return {"configurable": {"thread_id": conversation_id}}
