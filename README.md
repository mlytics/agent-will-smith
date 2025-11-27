# Agent-Will-Smith API Server

FastAPI server with Google Gemini backend. Maintains compatibility with existing Vext API contract.

**Model**: Gemini 2.5 Flash Lite ($0.1/$0.4 per 1M tokens) - Cost-optimized choice vs Vext ($1/$1)

## Features

- **Five Core Endpoints**: `/generateQuestions`, `/getMetadata`, `/getAnswer`, `/eeat`, `/summarize`
- **Gemini Integration**: Google Gemini for LLM operations
- **E-E-A-T Assessment**: Content quality analysis based on Google's Search Quality Rater Guidelines
- **Multi-Language Support**: Questions and answers in multiple languages via `lang` parameter
- **File-based Caching**: Automatic caching with no setup required
- **Streaming Support**: Server-Sent Events (SSE) for real-time answer generation
- **API Compatibility**: Maintains exact request/response format from Vext API

## Prerequisites

- Python 3.11+ (3.11/3.12 recommended)
- Google Gemini API key ([Get one here](https://ai.google.dev/))

## Quick Start

### Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install uv if you haven't already
pip install uv

# Sync dependencies (creates virtual environment and installs all dependencies)
uv sync
```

**Alternative (without uv):**
```bash
pip install -e .
```

### Configuration

Create `.env` file:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here
API_BEARER_TOKEN=change_me
ALLOWED_ORIGINS=https://your-allowed-origin.com

# Optional
GEMINI_MODEL=gemini-2.5-flash-lite  # Cost: $0.1/$0.4 per 1M tokens
HOST=0.0.0.0
PORT=8888
LOG_LEVEL=INFO

# Google Custom Search (optional - only for related sources)
GOOGLE_SEARCH_KEY=
GOOGLE_SEARCH_ENGINE_ID=
```

### Run

```bash
# Development
uv run python run.py

# Or with Docker
docker compose up --build
```

Server starts on `http://localhost:8888`

### Health Check

```bash
curl http://localhost:8888/health
```

## API Endpoints

All POST endpoints require `Authorization: Bearer <token>` header.

### POST /generateQuestions

Generate 1-5 questions from URL or content.

**Request:**
```json
{
  "inputs": {
    "url": "https://example.com/article",
    "context": "Optional: direct content text",
    "prompt": "Optional: custom prompt",
    "lang": "zh-tw",
    "previous_questions": []
  },
  "user": "test_user",
  "type": "answer_page",
  "source_url": "https://example.com/article"
}
```

**Response:**
```json
{
  "task_id": "1d779a47-b403-427f-b4b4-9120d9841175",
  "data": {
    "status": "succeeded",
    "outputs": {
      "result": {
        "question_1": "Question text 1",
        "question_2": "Question text 2"
      },
      "content_id": "56e71457-c55d-4b13-bc8a-205cbdb42673"
    },
    "elapsed_time": 1.6,
    "created_at": 1761248073,
    "finished_at": 1761248075
  }
}
```

**Notes:**
- If both `url` and `context` are provided, `context` takes precedence
- `content_id` can be used in `/getAnswer` for session continuity
- Default language is `zh-tw` if `lang` is omitted

### POST /getMetadata

Extract metadata (tags, images, sources) from URL with domain filtering.

**Request:**
```json
{
  "inputs": {
    "url": "https://example.com/article",
    "query": "Optional search query",
    "tag_prompt": "Optional: custom tag generation prompt"
  },
  "user": "test_user"
}
```

**Response:**
```json
{
  "task_id": "1f802502-0c9c-4733-87fb-0a2499af6cbb",
  "data": {
    "status": "succeeded",
    "outputs": {
      "tag": "tag1, tag2, tag3",
      "images": [{"images": "{\"images\": []}"}],
      "sources": [{"sources": "{\"citations\": [...]}"}]
    },
    "elapsed_time": 2.41,
    "created_at": 1761245271,
    "finished_at": 1761245273
  }
}
```

**Notes:**
- Search results are automatically filtered to match the input URL's domain
- Domain is normalized (e.g., `m.cnyes.com` → `cnyes.com`)

### POST /getAnswer

Generate answer with optional SSE streaming. Supports `content_id` from `/generateQuestions` for session continuity.

**Request:**
```json
{
  "inputs": {
    "query": "Your question",
    "url": "https://example.com/article",
    "content_id": "Optional: from generateQuestions response",
    "prompt": "Optional: custom prompt",
    "lang": "zh-tw"
  },
  "user": "test_user",
  "stream": false
}
```

**Response (non-streaming):**
```json
{
  "event": "workflow_finished",
  "task_id": "9737ff45-e015-4e2d-8505-c7525a655d50",
  "data": {
    "status": "succeeded",
    "outputs": {
      "summary": "Generated answer text...",
      "citations": [...],
      "citation_type": "cached"
    },
    "elapsed_time": 3.7,
    "created_at": 1761248666,
    "finished_at": 1761248670
  }
}
```

**Response (streaming):**
Set `"stream": true` to receive Server-Sent Events:
- `workflow_started` - Workflow begins
- `token_chunk` - Streaming answer chunks
- `citations` - Citation information
- `workflow_finished` - Final response

**Error Handling:**
- If `content_id` is provided but not found, returns `"status": "failed"` with empty `outputs: {}`
- If both `url` and `content_id` are empty, returns `"status": "failed"`

### POST /eeat

Assess E-E-A-T (Experience, Expertise, Authoritativeness, Trust) quality of content.

**Request:**
```json
{
  "inputs": {
    "input_type": "url",
    "url": "https://example.com/article",
    "content": "Optional: direct content (if input_type is 'content')",
    "metadata": {
      "author": "Optional: author name",
      "publish_date": "Optional: YYYY-MM-DD",
      "topic_category": "Optional: medical|financial|general"
    }
  },
  "user": "test_user"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "overall_level": "High E-E-A-T",
    "scores": {
      "experience": {"level": "High", "confidence": 0.85, "rationale": [...]},
      "expertise": {"level": "High", "confidence": 0.78, "rationale": [...]},
      "authoritativeness": {"level": "High", "confidence": 0.92, "rationale": [...]},
      "trust": {"level": "Trustworthy", "confidence": 0.88, "rationale": [...]}
    },
    "page_quality_rating": "High",
    "is_ymyl": true,
    "evidence_summary": {...},
    "recommendations": [...]
  },
  "metadata": {
    "analyzed_at": "2025-11-15T10:30:00Z",
    "processing_time_ms": 2340,
    "content_length": 2500,
    "language": "en"
  }
}
```

**Notes:**
- Use `input_type: "url"` to analyze from URL, or `input_type: "content"` for direct text
- Both `/eeat` and `/api/v1/content/eeat-assessment` endpoints are available

### POST /summarize

Generate comprehensive summaries for articles (designed for Intent Engine integration).

**Request:**
```json
{
  "title": "Article title",
  "content": "Full article content text...",
  "author": "Optional: author name",
  "publish_time": "Optional: ISO 8601 timestamp",
  "keywords": ["Optional", "array", "of", "keywords"],
  "category": "Optional: category name",
  "permalink": "Optional: article URL"
}
```

**Response:**
```json
{
  "full_summary": "Comprehensive 2-3 paragraph summary...",
  "bullet_summary": ["Key point 1", "Key point 2", ...],
  "semantic_paragraphs": {
    "paragraphs": [
      {"text": "...", "semantic_role": "introduction"},
      {"text": "...", "semantic_role": "body"},
      {"text": "...", "semantic_role": "conclusion"}
    ]
  },
  "entities": {
    "persons": [...],
    "organizations": [...],
    "locations": [...]
  },
  "labels": {
    "topics": [...],
    "sentiment": "positive",
    "category": "金融",
    "content_type": "news"
  }
}
```

## Language Support

The API supports multiple languages through the `lang` parameter in `/generateQuestions` and `/getAnswer` endpoints.

**Supported Languages:** `en`, `zh-tw` (default), `zh-cn`, `zh`, `es`, `fr`, `de`, `it`, `pt`, `ja`, `ko`, `ru`, `ar`, `hi`, `th`, `vi`, `id`, `nl`, `pl`, `tr`

**Usage:**
```json
{
  "inputs": {
    "url": "https://example.com/article",
    "lang": "en"  // or "ja", "es", etc.
  }
}
```

If `lang` is omitted, defaults to `"zh-tw"`. Language code is case-insensitive.

## Caching

- **File-based caching**: Automatic caching using `./cache` directory
- Cache files stored as JSON
- No additional setup required
- Results are cached to improve response times

## Testing

```bash
# Install test dependencies
uv sync --extra test

# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=app --cov=services -v
```

**Test Configuration:**
- `TEST_DOMAIN`: Test URL for API endpoints (default: `https://m.cnyes.com/news/id/5627491`)
- `TEST_BASE_URL`: Base URL for domain extraction tests (default: `https://m.cnyes.com`)

## Deployment

### Development

```bash
uv run python run.py
```

### Production

```bash
uvicorn app:app --host 0.0.0.0 --port 8888 --workers 4
```

### Docker

```bash
# Build and run
docker compose up --build

# Or manually
docker build -t aigc-api-server .
docker run -p 8888:8888 --env-file .env aigc-api-server
```

### Google Cloud Run

```bash
./deploy-cloudrun.sh
```

## Security

- **Bearer Token Authentication**: All POST endpoints require `Authorization: Bearer <token>`
  - Configure via `API_BEARER_TOKEN` environment variable
  - If unset (local development), authentication is skipped with a warning
- **CORS**: Control allowed origins via `ALLOWED_ORIGINS` (comma-separated)
  - If omitted, only localhost origins are allowed
- **Secrets**: Store sensitive values in your deployment platform's secret manager

## Troubleshooting

### Installation Issues

- **Python 3.13 Rust errors**: Use pre-built wheels or use Python 3.11/3.12
- **Missing modules**: `uv sync` (or `pip install -e .` if not using uv)

### Connection Issues

- **API key invalid**: Check `.env` file contains correct `GEMINI_API_KEY`
- **Connection timeout**: Check firewall, VPN, or network restrictions

### Server Issues

- **Port in use**: Change `PORT` in `.env` or kill process using port 8888
- **Import errors**: Verify all dependencies installed: `uv sync`

## Project Structure

```
app.py                    # FastAPI main application
├── services/
│   ├── gemini_service.py    # Gemini API integration
│   ├── search_service.py    # Google Search & web scraping
│   ├── cache_service.py     # File-based caching
│   └── content_service.py   # Content fetching
└── pyproject.toml          # Python dependencies (uv/pip)
```

## License

MIT
