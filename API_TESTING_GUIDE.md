# 🚀 RAG Engine API & Swagger UI Testing Guide

Comprehensive testing guide for all API endpoints in the **RAG Engine** project with **Swagger UI payloads, input fields, cURL examples, actual database entity names, and expected responses**.

- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Base URL:** `http://127.0.0.1:8000`

---

## 🏷️ Real Active Entity Names in Your Neo4j Database

You can copy and paste any of these entity names into Swagger UI for Section 5 (`/v1/graph/entities/{entity_name}/related`) and Section 6 (`/v1/graph/entities/{entity_name}/documents`):

- **`JavaScript`**
- **`Google`**
- **`VS Code`**
- **`Flutter SDK`**
- **`Microsoft Windows`**
- **`SQLite`**
- **`Cloud Firestore`**
- **`Android SDK`**
- **`ANDROID STUDIO`**
- **`Java`**
- **`HTML`**
- **`Tutorials Point (I) Pvt. Ltd.`**

---

## 📋 Quick API Overview

| Method | Endpoint Path | Description | Swagger UI Input |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Server Health Status | *None* |
| `POST` | `/v1/file/upload` | Upload PDF for Ingestion | `file` (File selector button) |
| `GET` | `/v1/query` | Ask Query to RAG Engine | `q` (Text input) |
| `GET` | `/v1/graph/health` | Neo4j Connection & Stats | *None* |
| `GET` | `/v1/graph/entities/{entity_name}/related` | Get Related Graph Entities | `entity_name` (Text input) |
| `GET` | `/v1/graph/entities/{entity_name}/documents` | Get Documents Mentioning Entity | `entity_name` (Text input) |

---

## 1. Root Server Status (`GET /`)

### 🖥️ Swagger UI Instructions:
1. Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
2. Click on the **`GET /`** endpoint bar.
3. Click **Try it out** → Click **Execute**.

#### **Swagger UI Input Fields:**
- *No parameters required.*

#### **cURL Command:**
```bash
curl -X 'GET' 'http://127.0.0.1:8000/' -H 'accept: application/json'
```

#### **Expected Response (200 OK):**
```json
{
  "status": "running",
  "version": "v1"
}
```

---

## 2. Ingest PDF Document (`POST /v1/file/upload`)

### 🖥️ Swagger UI Instructions:
1. Under the **Ingestion** tag, click on **`POST /v1/file/upload`**.
2. Click **Try it out**.
3. In the **`file`** input row, click **Choose File** (or **Browse**) and select a `.pdf` file from your computer.
4. Click **Execute**.

#### **Swagger UI Payload / Input:**
- **`file`**: `Choose File -> select document.pdf`

#### **cURL Command:**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/file/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/path/to/your/file.pdf;type=application/pdf'
```

#### **Expected Response (200 OK):**
```json
{
  "status": "document ingested",
  "filename": "sample_document.pdf"
}
```

#### **Error Response (400 Bad Request):**
```json
{
  "detail": "Only PDF files are supported"
}
```

---

## 3. Query RAG System (`GET /v1/query`)

### 🖥️ Swagger UI Instructions:
1. Under the **Query** tag, click on **`GET /v1/query`**.
2. Click **Try it out**.
3. Type your question in the **`q`** text parameter box.
4. Click **Execute**.

#### **Swagger UI Payload / Input Sample 1:**
- **`q`**: `What is the summary of the ingested document?`

#### **Swagger UI Payload / Input Sample 2:**
- **`q`**: `What are the key entities or topics discussed?`

#### **cURL Command:**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/query?q=What%20is%20the%20summary%20of%20the%20ingested%20document%3F' \
  -H 'accept: application/json'
```

#### **Expected Response (200 OK):**
```json
{
  "query": "What is the summary of the ingested document?",
  "answer": "Based on the uploaded document, the main topics covered include vector embedding storage in Weaviate Cloud and Knowledge Graph entity extraction in Neo4j.",
  "sources_used": 4
}
```

---

## 4. Check Neo4j Graph Health (`GET /v1/graph/health`)

### 🖥️ Swagger UI Instructions:
1. Under the **Graph** tag, click on **`GET /v1/graph/health`**.
2. Click **Try it out** → Click **Execute**.

#### **Swagger UI Input Fields:**
- *No parameters required.*

#### **cURL Command:**
```bash
curl -X 'GET' 'http://127.0.0.1:8000/v1/graph/health' -H 'accept: application/json'
```

#### **Expected Response (200 OK):**
```json
{
  "enabled": true,
  "connected": true,
  "counts": {
    "documents": 1,
    "entities": 501,
    "mentions": 501
  }
}
```

---

## 5. Get Related Graph Entities (`GET /v1/graph/entities/{entity_name}/related`)

### 🖥️ Swagger UI Instructions:
1. Under the **Graph** tag, click on **`GET /v1/graph/entities/{entity_name}/related`**.
2. Click **Try it out**.
3. Type one of the active entity names in the **`entity_name`** field.
4. Click **Execute**.

#### **Swagger UI Payload / Input Sample 1:**
- **`entity_name`**: `JavaScript`

#### **Actual Response Output (`200 OK`):**
```json
{
  "entity": "JavaScript",
  "related": [
    {
      "name": "Flutter",
      "type": "PRODUCT"
    },
    {
      "name": "Windows",
      "type": "PRODUCT"
    },
    {
      "name": "Tutorials Point (I) Pvt. Ltd.",
      "type": "ORGANIZATION"
    },
    {
      "name": "MacOS",
      "type": "PRODUCT"
    },
    {
      "name": "ANDROID STUDIO",
      "type": "PRODUCT"
    }
  ]
}
```

#### **Swagger UI Payload / Input Sample 2:**
- **`entity_name`**: `Google`

#### **Actual Response Output (`200 OK`):**
```json
{
  "entity": "Google",
  "related": [
    {
      "name": "Cloud Firestore",
      "type": "PRODUCT"
    },
    {
      "name": "Android SDK",
      "type": "PRODUCT"
    },
    {
      "name": "Flutter SDK",
      "type": "PRODUCT"
    }
  ]
}
```

#### **cURL Command:**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/graph/entities/JavaScript/related' \
  -H 'accept: application/json'
```

---

## 6. Get Documents Mentioning Entity (`GET /v1/graph/entities/{entity_name}/documents`)

### 🖥️ Swagger UI Instructions:
1. Under the **Graph** tag, click on **`GET /v1/graph/entities/{entity_name}/documents`**.
2. Click **Try it out**.
3. Type the entity name in the **`entity_name`** field.
4. Click **Execute**.

#### **Swagger UI Payload / Input Sample:**
- **`entity_name`**: `Google`

#### **cURL Command:**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/graph/entities/Google/documents' \
  -H 'accept: application/json'
```

#### **Expected Response (200 OK):**
```json
{
  "entity": "Google",
  "documents": [
    "data/4f9b8c2d_tech_report.pdf"
  ]
}
```

---

## 💡 Quick Swagger UI Testing Flow

1. Open `http://127.0.0.1:8000/docs` in your browser.
2. Go to **`POST /v1/file/upload`** → Upload a PDF file → Click **Execute**.
3. Watch the step-by-step colored logs in your terminal as vector embeddings and Neo4j graph nodes are written!
4. Go to **`GET /v1/query`** → Type `q = Summarize the document` → Click **Execute**.
5. Go to **`GET /v1/graph/entities/JavaScript/related`** → Enter `JavaScript` or `Google` → Click **Execute**.
