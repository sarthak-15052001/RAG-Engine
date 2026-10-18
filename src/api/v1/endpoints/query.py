from fastapi import APIRouter, HTTPException

from src.core.logging_config import get_logger
from src.querying import retrieve_docs, generate_answer

logger = get_logger('api.query')
router = APIRouter(prefix='/v1', tags=['Query'])


@router.get('/query', summary='Ask a query to RAG system', tags=['Query'])
def query(q: str):
    logger.info(f'❓ [API QUERY] Incoming search query: "{q}"')

    try:
        docs = retrieve_docs(q)
    except Exception as exc:
        logger.error(f'❌ [API QUERY] Document retrieval failed for query "{q}": {exc}')
        raise HTTPException(status_code=500, detail=f'Retrieval failed: {exc}') from exc

    context = '\n'.join(docs)

    try:
        answer = generate_answer(context, q)
    except Exception as exc:
        logger.error(f'❌ [API QUERY] Answer generation failed for query "{q}": {exc}')
        raise HTTPException(status_code=500, detail=f'Answer generation failed: {exc}') from exc

    logger.info(f'✅ [API QUERY] Successfully answered query "{q}" (used {len(docs)} context chunk(s)).')
    return {'query': q, 'answer': answer, 'sources_used': len(docs)}
