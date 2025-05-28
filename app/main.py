import asyncio
import logging
import os
from contextlib import asynccontextmanager

import pyfiglet
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utilities import envs

load_dotenv()

from app.api.routes import router
from app.databases import database

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting App!\n")

    init_db()

    log.info("\n" + pyfiglet.figlet_format("RL MCP"))
    yield

    log.info("Shutting down App!\n")

    handle_pending_tasks()

    log.info("Shut down complete!\n")


def init_loggers():
    log_level = logging._nameToLevel.get(
        os.environ.get("LOGGING_LEVEL", "INFO").upper()
    )
    logging.getLogger().setLevel(log_level)

    uvicorn_logger = logging.getLogger("uvicorn.error")
    uvicorn_logger.setLevel(logging.WARNING)

    logging.info(
        f"Initialized root logger with level {logging.getLevelName(logging.root.level)}"
    )


def init_db():
    log.info("Initializing DB...")

    database.establish_connection()
    database.migrate()

    log.info("DB initialization complete\n")


def handle_pending_tasks():
    log.info("Handling pending tasks...")
    loop = asyncio.get_event_loop()
    pending = asyncio.all_tasks(loop)

    if not pending:
        log.info("No pending tasks\n")
        return

    log.info(f"Shutting down with {len(pending)} pending tasks:")
    for t in pending:
        log.info(f"  {t}")


def handle_disconnect():
    log.info("Disconnecting from DB...")
    database.ensure_disconnect()
    log.info("Disconnection complete\n")


try:
    init_loggers()

    if envs.get_env() in envs.HOSTED_ENVS:
        log.info("Starting app in hosted mode\n")
        app = FastAPI(
            lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None
        )
    else:
        log.info("Starting app in local mode\n")
        app = FastAPI(lifespan=lifespan)

    app.include_router(router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

except Exception as e:
    logging.critical(f"Error loading app: {e}", exc_info=True)
