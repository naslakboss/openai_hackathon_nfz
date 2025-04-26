from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv
from app.bot.router import router as bot_router

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

if not load_dotenv():
    logger.error("Problem loading .env file. Failing silently for now!")
    # raise Exception("Problem loading .env file")
else:
    logger.info("Loaded .env file")


def create_app() -> FastAPI:
    app = FastAPI(openapi_prefix="/api")  # type: ignore
    app.include_router(bot_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("Started application")
    return app
