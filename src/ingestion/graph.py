from src.core.logging_config import get_logger
from src.ingestion.ingestion_pipelines import build_ingestion_pipeline

logger = get_logger('ingestion.pipeline')


def ingest_file(file_path):
    logger.info(f'🏁 [INGESTION] Starting full RAG ingestion pipeline for: {file_path}')
    pipeline = build_ingestion_pipeline()
    result = pipeline.invoke({'file': file_path})
    logger.info(f'🎉 [INGESTION] Ingestion pipeline execution finished successfully for: {file_path}')
    return result
