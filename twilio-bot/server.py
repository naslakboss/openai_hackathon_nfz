#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import argparse
import json
import os

import uvicorn
from bot import run_bot
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def start_call_get():
    print("GET TwiML")
    print("Current working directory:", os.getcwd())
    return HTMLResponse(content=open("templates/streams.xml").read(), media_type="application/xml")


@app.post("/")
async def start_call(request: Request):
    print("POST TwiML")
    print("Current working directory:", os.getcwd())
    
    form_data = await request.form()
    caller_number = form_data.get("From")
    print(f"Caller number from POST: {caller_number}", flush=True)
    
    return HTMLResponse(content=open("templates/streams.xml").read(), media_type="application/xml")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    start_data = websocket.iter_text()
    await start_data.__anext__()
    call_data = json.loads(await start_data.__anext__())
    print(call_data, flush=True)
    stream_sid = call_data["start"]["streamSid"]
    
    caller_number = None
    if "start" in call_data and "customParameters" in call_data["start"]:
        caller_number = call_data["start"]["customParameters"].get("From")
    
    print(f"Caller number: {caller_number}", flush=True)
    print("WebSocket connection accepted")
    await run_bot(websocket, stream_sid, True, caller_number)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipecat Twilio Chatbot Server")
    parser.add_argument(
        "-t", "--test", action="store_true", default=False, help="set the server in testing mode"
    )
    args, _ = parser.parse_known_args()

    uvicorn.run(app, host="0.0.0.0", port=8765)
