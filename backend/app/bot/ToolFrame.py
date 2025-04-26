
from pipecat.frames.frames import DataFrame
from langchain_core.messages import BaseMessage

class LangchainMessageFrame(DataFrame):
    def __init__(self, message: BaseMessage):
        super().__init__()
        self.message = message

    def __str__(self):
        return f"LangchainMessageFrame(message={self.message})"