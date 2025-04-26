#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import datetime
import io
import os
import sys
import wave
from pipecat.services.groq import GroqSTTService
from pipecat.transcriptions.language import Language
import aiofiles
from dotenv import load_dotenv
from fastapi import WebSocket
from loguru import logger
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantResponseAggregator,
    LLMUserResponseAggregator,
)
from pipecat.frames.frames import LLMMessagesFrame
from OpenAiAgentProcessor import OpenAiAgentProcessor

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="CRITICAL")


async def save_audio(server_name: str, audio: bytes, sample_rate: int, num_channels: int):
    if len(audio) > 0:
        filename = (
            f"{server_name}_recording_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        )
        with io.BytesIO() as buffer:
            with wave.open(buffer, "wb") as wf:
                wf.setsampwidth(2)
                wf.setnchannels(num_channels)
                wf.setframerate(sample_rate)
                wf.writeframes(audio)
            async with aiofiles.open(filename, "wb") as file:
                await file.write(buffer.getvalue())
        logger.info(f"Merged audio saved to {filename}")
    else:
        logger.info("No audio data to save")


async def run_bot(websocket_client: WebSocket, stream_sid: str, testing: bool, caller_number: str = None):
    transport = FastAPIWebsocketTransport(
        websocket=websocket_client,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
            serializer=TwilioFrameSerializer(stream_sid),
        ),
    )

    stt = get_stt()
    tts = get_tts()
    
    openai_agent_processor = OpenAiAgentProcessor(participant_id="a", caller_number=caller_number)
    user_agg = LLMUserResponseAggregator()
    assistant_agg = LLMAssistantResponseAggregator()

    audiobuffer = AudioBufferProcessor(user_continuous_stream=not testing)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,  
            user_agg,

            openai_agent_processor,

            tts, 
            transport.output(),
            audiobuffer,
            assistant_agg,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=8000,
            audio_out_sample_rate=8000,
            allow_interruptions=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        # Start recording.
        await audiobuffer.start_recording()
        msg = {
            "role": "system",
            "content": "Please introduce yourself to the user in one shortsentance.",
        }
        frame = LLMMessagesFrame([msg])
        await task.queue_frames([frame])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        await task.cancel()

    @audiobuffer.event_handler("on_audio_data")
    async def on_audio_data(buffer, audio, sample_rate, num_channels):
        server_name = f"server_{websocket_client.client.port}"
        await save_audio(server_name, audio, sample_rate, num_channels)

    # We use `handle_sigint=False` because `uvicorn` is controlling keyboard
    # interruptions. We use `force_gc=True` to force garbage collection after
    # the runner finishes running a task which could be useful for long running
    # applications with multiple clients connecting.
    runner = PipelineRunner(handle_sigint=False, force_gc=True)

    await runner.run(task)

def get_tts():
    return ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id="Xb7hH8MSUJpSbSDYk0k2",
        sample_rate=24000,
        params=ElevenLabsTTSService.InputParams(language=Language.PL),
    )


def get_stt():
    return GroqSTTService(
        model="whisper-large-v3-turbo",
        api_key=os.getenv("GROQ_API_KEY"),
        language=Language.PL,
        prompt="Transcribe the following conversation",
        temperature=0.0,
    )
