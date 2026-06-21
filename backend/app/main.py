import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.jobs.scheduler import PipelineScheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

settings = get_settings()
pipeline_scheduler = PipelineScheduler(settings=settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).info("Starting %s", settings.app_name)
    init_db()
    if settings.scheduler_enabled:
        pipeline_scheduler.start()
    yield
    pipeline_scheduler.shutdown()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
