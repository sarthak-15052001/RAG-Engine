from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.config import (
    ENABLE_GRAPH_EXTRACTION,
    WEAVIATE_BATCH_SIZE,
    ENTITY_EXTRACTION_CONCURRENCY,
)
from src.core.logging_config import get_logger
from src.data_stores.weaviate_client import load_pdf, split_documents, store_vectors
from src.data_stores.neo4j_graph_client import store_document_entities
from src.utils.entity_extractor import extract_entities
from src.ingestion.jobs import job_store

logger = get_logger('ingestion.nodes')


def load_node(state):
    file_path = state['file']
    logger.info(f'🔄 [NODE: LOAD] Starting PDF loading step for: {file_path}')
    docs = load_pdf(file_path)
    logger.info(f'✅ [NODE: LOAD] PDF loading step completed. ({len(docs)} pages loaded)')
    return {'docs': docs}


def split_node(state):
    logger.info('🔄 [NODE: SPLIT] Starting document splitting step...')
    chunks = split_documents(state['docs'])
    job_id = state.get('job_id')
    if job_id:
        job_store.update(job_id, total_chunks=len(chunks))
    logger.info(f'✅ [NODE: SPLIT] Document splitting completed. ({len(chunks)} chunks created)')
    return {'chunks': chunks}


def store_node(state):
    logger.info('🔄 [NODE: WEAVIATE STORE] Starting Weaviate vector store embedding & storage step...')
    job_id = state.get('job_id')

    def on_progress(stored, failed, total):
        if job_id:
            job_store.update(job_id, chunks_stored=stored, chunks_failed=failed)

    stored, failed = store_vectors(
        state['chunks'],
        batch_size=WEAVIATE_BATCH_SIZE,
        on_progress=on_progress,
    )
    logger.info(f'✅ [NODE: WEAVIATE STORE] Weaviate storage step completed. ({stored} stored, {failed} failed)')
    return {'stored': True, 'vectors_stored': stored, 'vectors_failed': failed}


def _extract_entities_for_chunk(chunk):
    return extract_entities(chunk.page_content)


def graph_node(state):
    """Extracts named entities from each chunk and stores them in Neo4j."""
    if not ENABLE_GRAPH_EXTRACTION:
        logger.info('ℹ️ [NODE: NEO4J GRAPH] Graph extraction is disabled via config (ENABLE_GRAPH_EXTRACTION=false). Skipping step.')
        return {'graph_entities_stored': 0}

    job_id = state.get('job_id')
    chunks = state['chunks']
    file_path = state['file']
    seen = {}
    failed_chunks = 0

    logger.info(
        f'🧠 [NODE: NEO4J GRAPH] Extracting entities from {len(chunks)} chunk(s) '
        f'using {ENTITY_EXTRACTION_CONCURRENCY} concurrent threads...'
    )

    with ThreadPoolExecutor(max_workers=ENTITY_EXTRACTION_CONCURRENCY) as pool:
        futures = {pool.submit(_extract_entities_for_chunk, chunk): chunk for chunk in chunks}
        for future in as_completed(futures):
            try:
                entities = future.result()
            except Exception:
                failed_chunks += 1
                continue
            for entity in entities:
                seen[(entity.name, entity.type)] = entity

    entities = [{'name': name, 'type': etype} for (name, etype) in seen.keys()]
    logger.info(f'✨ [NODE: NEO4J GRAPH] Extracted {len(entities)} unique named entity(ies) across chunks (Failed chunk extractions: {failed_chunks}).')

    try:
        store_document_entities(file_path, entities)
    except Exception as exc:
        logger.error(f'❌ [NODE: NEO4J GRAPH] Failed to write graph entities to Neo4j: {exc}')
        if job_id:
            job_store.update(
                job_id,
                entities_stored=0,
                graph_error=f'{type(exc).__name__}: {exc}',
            )
        return {'graph_entities_stored': 0}

    if job_id:
        job_store.update(job_id, entities_stored=len(entities), graph_error=None)

    logger.info(f'✅ [NODE: NEO4J GRAPH] Knowledge Graph extraction & storage step completed. ({len(entities)} entities linked)')
    return {'graph_entities_stored': len(entities)}
