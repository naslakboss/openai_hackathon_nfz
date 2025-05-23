from agents import Agent, Runner, TResponseInputItem

from pipecat.frames.frames import (
    Frame,
    LLMMessagesFrame,
    TextFrame,
)

from openai.types.responses import ResponseTextDeltaEvent
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from minimal_example import nfz_agent
from minimal_example import send_sms_summary

class OpenAiAgentProcessor(FrameProcessor):
    def __init__(self, participant_id: str, caller_number: str = None):
        super().__init__()
        self._participant_id = participant_id
        self.caller_number = caller_number
        self.input_items: list[TResponseInputItem] = []
        self._agent = nfz_agent

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        send_sms_summary.caller_number = self.caller_number

        if isinstance(frame, LLMMessagesFrame):
            # Messages are accumulated on the context as a list of messages.
            # The last one by the human is the one we want to send to the LLM.
            text: str = frame.messages[-1]["content"]
            self.input_items.append({"content": text.strip(), "role": "user"})
            result = Runner.run_streamed(self._agent, input=self.input_items)
            
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
                    await self.push_frame(TextFrame(event.data.delta))
            
            self.input_items = result.to_input_list()


        else:
            await self.push_frame(frame, direction)
