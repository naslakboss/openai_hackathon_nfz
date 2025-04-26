from agents import Agent, Runner

from pipecat.frames.frames import (
    Frame,
    LLMMessagesFrame,
    TextFrame,
)

from openai.types.responses import ResponseTextDeltaEvent
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class OpenAiAgentProcessor(FrameProcessor):
    def __init__(self, participant_id: str):
        super().__init__()
        self._participant_id = participant_id
        self._agent = Agent(
            name="Joker",
            instructions="You are a helpful assistant.",
        )

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, LLMMessagesFrame):
            # Messages are accumulated on the context as a list of messages.
            # The last one by the human is the one we want to send to the LLM.
            text: str = frame.messages[-1]["content"]
            result = Runner.run_streamed(self._agent, input=text.strip())
            
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
                    await self.push_frame(TextFrame(event.data.delta))


        else:
            await self.push_frame(frame, direction)
