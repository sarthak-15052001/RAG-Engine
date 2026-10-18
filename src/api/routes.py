from fastapi import APIRouter
from src.api.v1.endpoints import ingest, query, graph

router = APIRouter()
router.include_router(ingest.router)
router.include_router(query.router)
router.include_router(graph.router)
