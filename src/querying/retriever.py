from src.core.logging_config import get_logger
from src.data_stores.weaviate_client import get_vectorstore

logger = get_logger('query.retriever')


def retrieve_docs(query, k=4):
    """Retrieve the top-k most relevant document chunks for a query from Weaviate."""
    logger.info(f'🔎 [RETRIEVER] Executing similarity search in Weaviate (k={k}) for query: "{query}"')
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search(query, k=k)
    logger.info(f'✅ [RETRIEVER] Retrieved {len(results)} matching document chunk(s) from Weaviate.')
    return [doc.page_content for doc in results]
