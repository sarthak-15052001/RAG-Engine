import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile

from src.core.config import UPLOAD_DIR
from src.core.logging_config import get_logger
from src.ingestion.graph import ingest_file

logger = get_logger('api.ingest')
router = APIRouter(prefix='/v1', tags=['Ingestion'])

ALLOWED_CONTENT_TYPES = {'application/pdf'}


@router.post('/file/upload', summary='Upload PDF for RAG ingestion', tags=['Ingestion'])
async def upload_pdf(file: UploadFile):
    logger.info(f'📁 [API INGEST] File upload request received: filename="{file.filename}", content_type="{file.content_type}"')

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(f'⚠️ [API INGEST] Rejected upload: unsupported content type "{file.content_type}"')
        raise HTTPException(status_code=400, detail='Only PDF files are supported')

    original_name = os.path.basename(file.filename or 'upload.pdf')
    if not original_name.lower().endswith('.pdf'):
        original_name += '.pdf'

    safe_name = f'{uuid.uuid4().hex}_{original_name}'

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, safe_name)

    contents = await file.read()
    if not contents:
        logger.warning('⚠️ [API INGEST] Rejected upload: file is empty')
        raise HTTPException(status_code=400, detail='Uploaded file is empty')

    with open(path, 'wb') as buffer:
        buffer.write(contents)

    logger.info(f'💾 [API INGEST] Saved upload to disk: {path} ({len(contents)} bytes). Triggering ingestion pipeline...')

    try:
        ingest_file(path)
    except Exception as exc:
        logger.error(f'❌ [API INGEST] Ingestion pipeline failed for "{original_name}": {exc}')
        raise HTTPException(status_code=500, detail=f'Ingestion failed: {exc}') from exc

    logger.info(f'🎉 [API INGEST] Successfully processed and ingested document: "{original_name}"')
    return {'status': 'document ingested', 'filename': original_name}
