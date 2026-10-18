from fastapi import APIRouter, HTTPException

from src.core.config import ENABLE_GRAPH_EXTRACTION
from src.core.logging_config import get_logger
from src.data_stores.neo4j_graph_client import (
    get_related_entities,
    get_documents_mentioning,
    get_graph_counts,
    verify_connectivity,
)

logger = get_logger('api.graph')
router = APIRouter(prefix='/v1/graph', tags=['Graph'])


@router.get('/health', summary='Check Neo4j connectivity and graph contents')
def graph_health():
    logger.info('🏥 [API GRAPH] Graph health check endpoint invoked.')
    if not ENABLE_GRAPH_EXTRACTION:
        logger.info('ℹ️ [API GRAPH] Graph extraction is disabled in configuration.')
        return {'enabled': False, 'connected': False}

    try:
        verify_connectivity()
    except Exception as exc:
        logger.error(f'❌ [API GRAPH] Neo4j connectivity check failed: {exc}')
        return {'enabled': True, 'connected': False, 'detail': str(exc)}

    try:
        counts = get_graph_counts()
    except Exception as exc:
        logger.error(f'❌ [API GRAPH] Failed to retrieve graph counts: {exc}')
        return {
            'enabled': True,
            'connected': True,
            'counts_error': f'Connected, but counting nodes failed: {exc}',
        }

    logger.info('✅ [API GRAPH] Graph health check passed.')
    return {'enabled': True, 'connected': True, 'counts': counts}


@router.get('/entities/{entity_name}/related', summary='Entities that co-occur with this entity')
def related_entities(entity_name: str):
    logger.info(f'🕸️ [API GRAPH] Fetching entities co-occurring with entity "{entity_name}"...')
    try:
        res = get_related_entities(entity_name)
        return {'entity': entity_name, 'related': res}
    except Exception as exc:
        logger.error(f'❌ [API GRAPH] Error retrieving related entities for "{entity_name}": {exc}')
        raise HTTPException(status_code=500, detail=f'Graph query failed: {exc}') from exc


@router.get('/entities/{entity_name}/documents', summary='Documents that mention this entity')
def documents_mentioning(entity_name: str):
    logger.info(f'📄 [API GRAPH] Fetching documents mentioning entity "{entity_name}"...')
    try:
        res = get_documents_mentioning(entity_name)
        return {'entity': entity_name, 'documents': res}
    except Exception as exc:
        logger.error(f'❌ [API GRAPH] Error retrieving documents for entity "{entity_name}": {exc}')
        raise HTTPException(status_code=500, detail=f'Graph query failed: {exc}') from exc
