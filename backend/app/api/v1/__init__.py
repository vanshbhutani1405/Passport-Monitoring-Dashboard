from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.clusters import router as clusters_router
from app.api.v1.health import router as health_router
from app.api.v1.posts import router as posts_router
from app.api.v1.search import router as search_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(posts_router)
api_router.include_router(clusters_router)
api_router.include_router(analytics_router)
api_router.include_router(search_router)


__all__ = ["api_router"]
