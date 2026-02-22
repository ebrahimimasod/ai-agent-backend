# RAG WordPress (Flask + Celery + Chroma)

A complete RAG (Retrieval-Augmented Generation) system that ingests WordPress posts, chunks them, creates embeddings, stores them in ChromaDB, and provides a chat interface for question answering.

## Architecture

- **API**: Flask
- **Worker**: Celery
- **Broker/Backend**: Redis
- **Database**: PostgreSQL
- **Vector DB**: ChromaDB
- **Embedding Providers**: OpenAI or Gemini
- **LLM Providers**: OpenAI or Gemini

## Setup

1. Copy `.env.example` to `.env` and fill in your configuration:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set:
   - `API_KEY`: Your API key for authentication
   - `WP_BASE_URL`: Your WordPress site URL
   - `OPENAI_API_KEY` or `GEMINI_API_KEY`: Your LLM provider API key
   - Other settings as needed

## Run

Start all services with Docker Compose:

```bash
docker compose up -d --build
```

The API will be available at `http://localhost:8001`

## API Endpoints

All endpoints require `X-API-Key` header for authentication.

### Health Check
```bash
GET /health
```

### Ingest WordPress Posts
```bash
POST /v1/ingest/run?full_resync=false
```
Returns: `{"job_id": "..."}`

### Check Ingest Job Status
```bash
GET /v1/ingest/jobs/{job_id}
```

### List Posts
```bash
GET /v1/posts?page=1&per_page=20
```

### Chat (RAG)
```bash
POST /v1/chat
Content-Type: application/json

{
  "question": "Your question here"
}
```
Returns: `{"answer": "...", "sources": [...]}`

## Example Usage

```bash
# Set your API key
export API_KEY="your-api-key"

# Run ingest
curl -X POST "http://localhost:8001/v1/ingest/run?full_resync=true" \
  -H "X-API-Key: $API_KEY"

# Ask a question
curl -X POST "http://localhost:8001/v1/chat" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this about?"}'
```

## Development

To view logs:
```bash
docker compose logs -f api
docker compose logs -f worker
```

To stop services:
```bash
docker compose down
```

To rebuild after code changes:
```bash
docker compose up -d --build
```
