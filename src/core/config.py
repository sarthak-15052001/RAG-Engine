import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

WEAVIATE_URL = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')
WEAVIATE_INDEX_NAME = os.getenv('WEAVIATE_INDEX_NAME', 'DocumentIndex')

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
CHAT_MODEL = os.getenv('CHAT_MODEL', 'gpt-4o-mini')

UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'data')

# Set to "true" to enable Neo4j entity-graph extraction during ingestion.
# Off by default so ingestion still works for people who only want vector
# search and haven't set up a Neo4j instance.
ENABLE_GRAPH_EXTRACTION = os.getenv('ENABLE_GRAPH_EXTRACTION', 'false').lower() == 'true'

# How many chunks to embed and write to Weaviate per batch. Keeps a single
# large PDF from being one giant all-or-nothing call.
WEAVIATE_BATCH_SIZE = int(os.getenv('WEAVIATE_BATCH_SIZE', '100'))

# How many entity-extraction LLM calls to run concurrently during ingestion.
# Entity extraction is one LLM call per chunk - run sequentially, a
# 1000-page PDF (thousands of chunks) would take hours. Keep this bounded
# so it doesn't blow through your OpenAI rate limits either.
ENTITY_EXTRACTION_CONCURRENCY = int(os.getenv('ENTITY_EXTRACTION_CONCURRENCY', '8'))
