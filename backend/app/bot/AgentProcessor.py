from typing import Optional, Union

from loguru import logger

from pipecat.frames.frames import (
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMMessagesFrame,
    TextFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from app.bot.CustomBroAgent import CustomBroAgent
from app.bot.ToolFrame import LangchainMessageFrame

try:
    from langchain_core.messages import AIMessageChunk, ToolMessage, HumanMessage
except ModuleNotFoundError as e:
    logger.exception(
        "In order to use Langchain, you need to `pip install pipecat-ai[langchain]`. "
    )
    raise Exception(f"Missing module: {e}")


class AgentProcessor(FrameProcessor):
    def __init__(self, agent: CustomBroAgent, participant_id: str):
        super().__init__()
        self._agent = agent
        self._participant_id = participant_id

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, LLMMessagesFrame):
            # Messages are accumulated on the context as a list of messages.
            # The last one by the human is the one we want to send to the LLM.
            logger.debug(f"Got transcription frame {frame}")
            text: str = frame.messages[-1]["content"]

            await self._ainvoke(text.strip())
        else:
            await self.push_frame(frame, direction)


    async def _ainvoke(self, text: str):
        logger.debug(f"Invoking chain with {text}")
        await self.push_frame(LLMFullResponseStartFrame())
        user_query = HumanMessage(content=text)
        await self.push_frame(LangchainMessageFrame(user_query))
        try:
            async for token in self._agent.chat_astream(
                [user_query],
                conversation_id=self._participant_id,
            ):
                match token:
                    case AIMessageChunk():
                        await self.push_frame(TextFrame(token.content))
                        await self.push_frame(LangchainMessageFrame(token))
                    # case ToolMessage():
                        # await self.push_frame(LangchainMessageFrame(token))
                    case _:
                        await self.push_frame(LangchainMessageFrame(token))
                        logger.info(f"Unexpected token type: {type(token)}, token: {token}")
        except GeneratorExit:
            logger.warning(f"{self} generator was closed prematurely")
        except Exception as e:
            logger.exception(f"{self} an unknown error occurred: {e}")
        finally:
            await self.push_frame(LLMFullResponseEndFrame())
