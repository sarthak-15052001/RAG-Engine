# RAG Engine (restructured)

## Project structure

- src/
  - main.py
  - config.py
  - core/
    - config.py
    - security.py
  - api/
    - routes.py
    - v1/endpoints/
      - ingest.py
      - query.py
  - graph_pipeline/
  - ingestion/
  - querying/
    - retriever.py
    - generator.py
  - data_stores/
    - weaviate_client.py

## Run

1. install dependencies:
   - `pip install -r requirements.txt`
2. run server:
   - `uvicorn src.main:app --reload`
3. endpoints:
   - `GET /`
   - `POST /v1/upload` (with file)
   - `GET /v1/query?q=...` (requires auth header `Authorization: Bearer <token>`, token validation stub)

## Tests

- `pytest -q`