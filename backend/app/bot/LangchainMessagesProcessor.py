from fastapi import WebSocket
from loguru import logger
from pipecat.frames.frames import (
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMMessagesFrame,
    TextFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from app.bot.ToolFrame import LangchainMessageFrame




class LangchainMessagesProcessor(FrameProcessor):
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, LangchainMessageFrame):
            logger.debug(f"Got tool call frame {frame}")
            await self.websocket.send_json(frame.message.model_dump())
        await self.push_frame(frame, direction)
