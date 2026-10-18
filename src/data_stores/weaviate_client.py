from urllib.parse import urlparse
from src.core.logging_config import get_logger

logger = get_logger('weaviate.client')

try:
    import weaviate
    _weaviate_available = True
    _connect_cloud = getattr(weaviate, 'connect_to_weaviate_cloud', None) or getattr(weaviate, 'connect_to_wcs', None)
    _weaviate_v4 = (_connect_cloud is not None) and hasattr(weaviate, 'connect_to_local')
except ImportError:
    weaviate = None
    _weaviate_available = False
    _connect_cloud = None
    _weaviate_v4 = False

try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_weaviate.vectorstores import WeaviateVectorStore
    _langchain_available = True
except ImportError:
    PyPDFLoader = None
    RecursiveCharacterTextSplitter = None
    OpenAIEmbeddings = None
    WeaviateVectorStore = None
    _langchain_available = False

from src.core.config import WEAVIATE_URL, WEAVIATE_API_KEY, WEAVIATE_INDEX_NAME, EMBEDDING_MODEL

_client = None


def _is_weaviate_cloud(url: str) -> bool:
    return '.weaviate.cloud' in url or '.weaviate.network' in url


def get_weaviate_client():
    """Lazily create and cache a v4 Weaviate client connection."""
    global _client
    if not _weaviate_available:
        raise RuntimeError(
            'The "weaviate-client" package is not installed. Run: pip install "weaviate-client>=4.5,<5"'
        )
    if not _weaviate_v4:
        installed_version = getattr(weaviate, '__version__', 'unknown')
        raise RuntimeError(
            f'Installed weaviate-client (version {installed_version}) is not v4. '
            f'Upgrade with: pip install --upgrade "weaviate-client>=4.5,<5"'
        )
    if _client is not None:
        return _client

    try:
        if _is_weaviate_cloud(WEAVIATE_URL):
            if not WEAVIATE_API_KEY:
                raise RuntimeError(
                    'WEAVIATE_URL points to Weaviate Cloud but WEAVIATE_API_KEY is not set.'
                )
            logger.info(f'🔌 [WEAVIATE] Connecting to Weaviate Cloud cluster at {WEAVIATE_URL}...')
            _client = _connect_cloud(
                cluster_url=WEAVIATE_URL,
                auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY),
            )
        else:
            parsed = urlparse(WEAVIATE_URL)
            host = parsed.hostname or 'localhost'
            port = parsed.port or (443 if parsed.scheme == 'https' else 8080)
            logger.info(f'🔌 [WEAVIATE] Connecting to local Weaviate instance at {host}:{port}...')
            _client = weaviate.connect_to_local(host=host, port=port)

        logger.info(f'✅ [WEAVIATE] Successfully connected to Weaviate (Live: {_client.is_live()}, Ready: {_client.is_ready()})')

    except Exception as exc:
        logger.error(f'❌ [WEAVIATE] Connection failed to {WEAVIATE_URL}: {exc}')
        raise RuntimeError(
            f'Could not connect to Weaviate at {WEAVIATE_URL}. '
            f'Is the URL correct and, if using Weaviate Cloud, is WEAVIATE_API_KEY set? ({exc})'
        ) from exc

    return _client


def close_weaviate_client():
    global _client
    if _client is not None:
        logger.info('🔌 [WEAVIATE] Closing active client connection...')
        _client.close()
        _client = None


def load_pdf(file_path):
    if not _langchain_available:
        raise RuntimeError('Required packages missing. Run: pip install langchain-community pypdf')
    logger.info(f'📄 [PDF LOAD] Opening and reading PDF file: {file_path}')
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    logger.info(f'✅ [PDF LOAD] Read {len(docs)} page(s) successfully.')
    return docs


def split_documents(docs):
    if not _langchain_available:
        raise RuntimeError('Required packages missing. Run: pip install langchain-text-splitters')
    logger.info(f'✂️ [TEXT SPLIT] Chunking {len(docs)} page(s) (chunk_size=1000, overlap=200)...')
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    logger.info(f'✅ [TEXT SPLIT] Generated {len(chunks)} chunk(s).')
    return chunks


def get_embeddings():
    if not _langchain_available:
        raise RuntimeError('Required packages missing. Run: pip install langchain-openai')
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)


def get_vectorstore_for_writing():
    if not _langchain_available:
        raise RuntimeError('Required packages missing. Run: pip install langchain-weaviate')
    client = get_weaviate_client()
    embeddings = get_embeddings()
    return WeaviateVectorStore(
        client=client,
        index_name=WEAVIATE_INDEX_NAME,
        text_key='text',
        embedding=embeddings,
    )


def store_vectors(docs, batch_size=100, on_progress=None):
    if not _langchain_available:
        raise RuntimeError('Required packages missing. Run: pip install langchain-weaviate')

    logger.info(f'💾 [WEAVIATE STORE] Embedding & storing {len(docs)} chunk(s) in index "{WEAVIATE_INDEX_NAME}"...')
    vectorstore = get_vectorstore_for_writing()

    stored = 0
    failed = 0
    total_batches = (len(docs) + batch_size - 1) // batch_size

    for idx, start in enumerate(range(0, len(docs), batch_size), start=1):
        batch = docs[start:start + batch_size]
        logger.info(f'   [WEAVIATE BATCH] Processing batch {idx}/{total_batches} ({len(batch)} chunks)...')
        try:
            vectorstore.add_documents(batch)
            stored += len(batch)
            logger.info(f'   [WEAVIATE BATCH] Batch {idx}/{total_batches} stored successfully. (Progress: {stored}/{len(docs)})')
        except Exception as exc:
            failed += len(batch)
            logger.error(f'❌ [WEAVIATE BATCH] Batch {idx}/{total_batches} failed: {exc}')

        if on_progress:
            on_progress(stored, failed, len(docs))

    logger.info(f'✅ [WEAVIATE STORE] Finished storing vectors: {stored} succeeded, {failed} failed.')
    return stored, failed


def get_vectorstore():
    if not _langchain_available:
        raise RuntimeError('Required packages missing. Run: pip install langchain-weaviate')
    client = get_weaviate_client()
    embeddings = get_embeddings()
    return WeaviateVectorStore(
        client=client,
        index_name=WEAVIATE_INDEX_NAME,
        text_key='text',
        embedding=embeddings,
    )
