"""
Central API Router

Aggregates all endpoint routers under the /api/v1 prefix.
"""

from fastapi import APIRouter

from app.api.endpoints import auth, upload, process, evaluate, results, knowledge

api_router = APIRouter()

# ---- Mount Endpoint Routers ----
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(process.router, prefix="/process", tags=["Processing"])
api_router.include_router(evaluate.router, prefix="/evaluate", tags=["Evaluation"])
api_router.include_router(results.router, prefix="/results", tags=["Results"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge Base"])
