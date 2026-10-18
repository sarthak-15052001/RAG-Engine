import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from src.core.config import ENABLE_GRAPH_EXTRACTION
from src.core.logging_config import setup_logging, get_logger
from src.api.routes import router
from src.data_stores.weaviate_client import close_weaviate_client
from src.data_stores.neo4j_graph_client import close_driver, ensure_constraints

# Initialize logging configuration
setup_logging()
logger = get_logger('api.server')


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('🚀 Starting RAG Engine API Server...')
    if ENABLE_GRAPH_EXTRACTION:
        try:
            logger.info('[NEO4J] Graph extraction is enabled. Ensuring schema constraints...')
            ensure_constraints()
            logger.info('[NEO4J] Constraints verified successfully.')
        except Exception as exc:
            logger.warning(f'[NEO4J] Could not initialize Neo4j constraints on startup: {exc}')
    else:
        logger.info('[NEO4J] Graph extraction is disabled (ENABLE_GRAPH_EXTRACTION=false).')

    yield

    logger.info('🛑 Shutting down RAG Engine API Server...')
    logger.info('[WEAVIATE] Closing Weaviate client connection...')
    close_weaviate_client()
    logger.info('[NEO4J] Closing Neo4j database driver...')
    close_driver()
    logger.info('👋 Server shutdown complete.')


app = FastAPI(title='RAG Engine API', lifespan=lifespan)


@app.middleware('http')
async def log_requests(request: Request, call_next):
    """Middleware to log every incoming API request and response status/duration."""
    start_time = time.time()
    path = request.url.path
    method = request.method
    query_params = dict(request.query_params)
    param_str = f" query={query_params}" if query_params else ""

    logger.info(f'📥 [API CALL] {method} {path}{param_str}')

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f'📤 [API RESP] {method} {path} -> {response.status_code} ({process_time:.1f}ms)')
        return response
    except Exception as exc:
        process_time = (time.time() - start_time) * 1000
        logger.error(f'💥 [API ERROR] {method} {path} -> Failed after {process_time:.1f}ms: {exc}')
        raise exc


app.include_router(router)


@app.get('/')
def root():
    return {'status': 'running', 'version': 'v1'}
