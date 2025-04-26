from fastapi import APIRouter, WebSocket
import logging
import uuid
import asyncio
import os

from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline

from pipecat.frames.frames import BotInterruptionFrame, EndFrame, LLMMessagesFrame
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.services.groq import GroqSTTService
from pipecat.transcriptions.language import Language


from pipecat.processors.aggregators.llm_response import (
    LLMAssistantResponseAggregator,
    LLMUserResponseAggregator,
)

from mcp import ClientSession, StdioServerParameters, stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools # type: ignore

from app.bot.CustomBroAgent import CustomBroAgent
from app.bot.AgentProcessor import AgentProcessor
from app.bot.LangchainMessagesProcessor import LangchainMessagesProcessor

router = APIRouter(prefix="/vo")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SessionTimeoutHandler:
    """Handles actions to be performed when a session times out.
    Inputs:
    - task: Pipeline task (used to queue frames).
    - tts: TTS service (used to generate speech output).
    """

    def __init__(self, task, tts):
        self.task = task
        self.tts = tts
        self.background_tasks = set()

    async def handle_timeout(self, client_address):
        """Handles the timeout event for a session."""
        try:
            logger.info(f"Connection timeout for {client_address}")

            # Queue a BotInterruptionFrame to notify the user
            await self.task.queue_frames([BotInterruptionFrame()])

            # Send the TTS message to inform the user about the timeout
            await self.tts.say(
                "I'm sorry, we are ending the call now. Please feel free to reach out again if you need assistance."
            )

            # Start the process to gracefully end the call in the background
            end_call_task = asyncio.create_task(self._end_call())
            self.background_tasks.add(end_call_task)
            end_call_task.add_done_callback(self.background_tasks.discard)
        except Exception as e:
            logger.error(f"Error during session timeout handling: {e}")

    async def _end_call(self):
        """Completes the session termination process after the TTS message."""
        try:
            # Wait for a duration to ensure TTS has completed
            await asyncio.sleep(15)

            # Queue both BotInterruptionFrame and EndFrame to conclude the session
            await self.task.queue_frames([BotInterruptionFrame(), EndFrame()])

            logger.info("TTS completed and EndFrame pushed successfully.")
        except Exception as e:
            logger.error(f"Error during call termination: {e}")



server_params = StdioServerParameters(
    command="npx",  # Executable
    args=["@playwright/mcp@latest"],  # Optional command line arguments
    env=None,  # Optional environment variables
)


# create web socket connection for chat
@router.websocket("/ws")
async def chat(websocket: WebSocket):
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            lang_tools = await load_mcp_tools(session)
            logger.info(f"Lang tools: {lang_tools}")

            logger.info("WebSocket connection accepted")

            agent = CustomBroAgent(tools=lang_tools)

            await start_conversation(websocket, agent)


async def start_conversation(websocket: WebSocket, agent: CustomBroAgent):
    logger.info("WebSocket connection accepted")
    await websocket.accept()
    conversation_id = str(uuid.uuid4())
    logger.info(f"Conversation ID: {conversation_id}")

    transport = get_transport(websocket)
    stt = get_stt()
    tts = get_tts()

    agent_processor = AgentProcessor(agent=agent, participant_id=conversation_id)

    user_agg = LLMUserResponseAggregator()
    assistant_agg = LLMAssistantResponseAggregator()
    langchain_message_processor = LangchainMessagesProcessor(websocket=websocket)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,  
            user_agg,
            agent_processor,
            langchain_message_processor,
            tts, 
            transport.output(),
            assistant_agg,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=16000,
            audio_out_sample_rate=16000,
            allow_interruptions=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport: FastAPIWebsocketTransport, client: WebSocket):  # type: ignore
        msg = {
            "role": "system",
            "content": "Please introduce yourself to the user in one shortsentance.",
        }
        frame = LLMMessagesFrame([msg])
        await task.queue_frames([frame])

    @transport.event_handler("on_session_timeout")
    async def on_session_timeout(transport: FastAPIWebsocketTransport, client: WebSocket):  # type: ignore
        logger.info(f"Entering in timeout for {client}")

    runner = PipelineRunner(handle_sigint=False) # FIXME: this is for development only
    logger.info(f"Running task for {conversation_id}")
    await runner.run(task)
    logger.info(f"Task finished for {conversation_id}")


def get_tts():
    return ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id="Xb7hH8MSUJpSbSDYk0k2",
        sample_rate=24000,
        params=ElevenLabsTTSService.InputParams(language=Language.EN),
    )


def get_stt():
    return GroqSTTService(
        model="whisper-large-v3-turbo",
        api_key=os.getenv("GROQ_API_KEY"),
        language=Language.EN,
        prompt="Transcribe the following conversation",
        temperature=0.0,
    )


def get_transport(websocket: WebSocket):
    return FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
            serializer=ProtobufFrameSerializer(),
        ),
    )
