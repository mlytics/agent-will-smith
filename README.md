# AIGC MVP API Server

Python FastAPI server that replaces the Vext API with Google Gemini backend. Maintains full compatibility with existing Laravel client code.

## Features

- **Three Core Endpoints**: 
  - `POST /generateQuestions` - Generate questions from content
  - `POST /getMetadata` - Extract metadata from URLs
  - `POST /getAnswer` - Generate answers with SSE streaming support

- **Gemini Integration**: Uses Google Gemini 2.0 Flash for LLM operations
- **Caching**: Multi-tier caching (Redis + file fallback)
- **Streaming**: Server-Sent Events (SSE) support for answer generation
- **Error Handling**: Robust error handling with retry logic
- **API Compatibility**: Maintains exact request/response format from Vext API

## Prerequisites

- Python 3.11, 3.12, or 3.13 (3.11/3.12 recommended)
- **Google Gemini API key** (REQUIRED) - [Get one here](https://ai.google.dev/)
- **Redis** (optional, for caching - file cache used as fallback)
- **Google Custom Search API** (optional, only for related source search - images, title, summary come from scraping the URL directly, not from Google Search)

## Quick Start

### 1. Install Dependencies

**For Python 3.11/3.12:**
```bash
pip install -r requirements.txt
```

**For Python 3.13:**
If you encounter Rust compilation errors, use pre-built wheels:
```bash
pip install --only-binary :all: -r requirements.txt
pip install --only-binary :all: lxml
```

### 2. Configure Environment

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key (minimum required):

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
```

See [Configuration](#configuration) section for all available options.

### 3. Run the Server

**Using the run script (recommended):**
```bash
python run.py
```

**Or using uvicorn directly:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8888 --reload
```

The server will start on `http://localhost:8888`

### 4. Test the Server

**Health Check:**
```bash
curl http://localhost:8888/health
```

**Test Endpoints:**
```bash
# Generate Questions
curl -X POST http://localhost:8888/generateQuestions \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"url": "https://example.com/article", "lang": "zh-tw"}, "user": "test_user"}'

# Get Metadata
curl -X POST http://localhost:8888/getMetadata \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"url": "https://example.com/article"}, "user": "test_user"}'

# Get Answer
curl -X POST http://localhost:8888/getAnswer \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"query": "What is this about?", "url": "https://example.com/article", "lang": "zh-tw"}, "user": "test_user", "stream": false}'
```

## Configuration

Edit `.env` file with your settings:

### Required Configuration

```env
# Google Gemini API Key (REQUIRED)
GEMINI_API_KEY=your_gemini_api_key_here

# Gemini model to use (optional, defaults to gemini-2.0-flash-exp)
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Optional Configuration

# Google Custom Search API (OPTIONAL - only for finding related sources in sources[] array)
# NOT REQUIRED - Without these:
#   - Images, title, summary, tags still work (extracted directly from URL's HTML)
#   - Only sources[] array will be empty (related search results)
# Leave empty if you don't need related source search functionality
GOOGLE_SEARCH_KEY=
GOOGLE_SEARCH_ENGINE_ID=

# Redis for caching (optional, file cache used as fallback)
REDIS_URL=redis://localhost:6379/0

# Cache directory for file-based caching
CACHE_DIR=./cache

# Server configuration
HOST=0.0.0.0
PORT=8888

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

See `.env.example` for all available configuration options with descriptions.

## Installation Troubleshooting

### Python 3.13 Rust Compilation Errors

If you see "metadata-generation-failed" or Rust-related errors with Python 3.13:

**Solution 1 (Recommended):** Use pre-built wheels:
```bash
pip install --only-binary :all: -r requirements.txt
pip install --only-binary :all: lxml
```

**Solution 2:** Install Rust from https://rustup.rs/, then install normally

**Solution 3:** Use Python 3.11 or 3.12 instead (easiest option)

### Other Common Issues

- **"No module named 'pydantic'"**: Run `pip install --upgrade pip && pip install -r requirements.txt`
- **lxml installation fails**: Try `pip install --only-binary lxml lxml`
- **Connection refused**: Ensure server is running on the correct port

## Laravel Integration

### Quick Integration

To use this new API server with your Laravel application, simply update the API host in `MyLib/MyAPI.php`:

```php
// Change line 14 from:
private $api_host = "https://mlytics-api.vextapp.com";

// To:
private $api_host = "https://your-api-server.com";  // Your new API server URL
```

**That's it!** No other changes needed. The API contract is identical.

### Environment-Based Configuration (Recommended)

For better flexibility, use environment variables in Laravel:

```php
// In MyAPI.php
private $api_host;

public function __construct($user = "")
{
    $this->api_host = env('AIGC_API_HOST', 'https://mlytics-api.vextapp.com');
    // ... rest of constructor
}
```

Then in Laravel `.env`:
```env
AIGC_API_HOST=https://your-api-server.com
```

### Feature Flag (For Gradual Rollout)

Add a feature flag for safe migration:

```php
// In MyAPI.php
public function __construct($user = "")
{
    if (env('FEATURE_AI_ORCHESTRATOR', false)) {
        $this->api_host = env('AIGC_API_HOST', 'https://your-api-server.com');
    } else {
        $this->api_host = env('VEXT_API_HOST', 'https://mlytics-api.vextapp.com');
    }
    // ... rest of constructor
}
```

### API Contract Compatibility

The new API server maintains 100% compatibility with the existing Vext API:

**Request Format:**
```json
{
  "inputs": {
    // endpoint-specific inputs
  },
  "user": "uuid_user",
  // optional fields
}
```

**Response Format:**
```json
{
  "event": "workflow_finished",
  "data": {
    "outputs": {
      // endpoint-specific outputs
    },
    "provider": "gemini-2.5-flash",
    "meta": {
      "tokens_used": 123,
      "latency_ms": 420,
      "cached": false
    }
  }
}
```

### Laravel Method Mapping

- `$myAPI->get_question(...)` → `POST /generateQuestions`
- `$myAPI->get_meta(...)` → `POST /getMetadata`
- `$myAPI->get_answer(...)` → `POST /getAnswer`

All existing Laravel code will work without modifications.

## API Endpoints

All endpoints match the existing Vext API contract for seamless integration.

### POST /generateQuestions

Generate 1-5 structured questions from content or URL.

**Request:**
```json
{
  "inputs": {
    "url": "https://example.com/article",
    "context": "Optional context text",
    "lang": "zh-tw",
    "previous_questions": []
  },
  "user": "uuid_user",
  "type": "answer_page"
}
```

**Response:**
```json
{
  "event": "workflow_finished",
  "data": {
    "outputs": {
      "result": [
        {"id": "q1", "text": "Question?", "type": "analytical", "confidence": 0.93}
      ]
    },
    "provider": "gemini-2.5-flash-lite",
    "meta": {
      "tokens_used": 123,
      "latency_ms": 420,
      "cached": false
    }
  }
}
```

### POST /getMetadata

Extract metadata from URL (title, summary, sources, tags, images).

**Request:**
```json
{
  "inputs": {
    "url": "https://example.com/article",
    "query": "Optional search query",
    "tag_prompt": "Generate 5 tags"
  },
  "user": "uuid_user"
}
```

**Response:**
```json
{
  "event": "workflow_finished",
  "data": {
    "outputs": {
      "url": "https://example.com/article",
      "domain": "example.com",
      "title": "Article Title",
      "summary": "Summary...",
      "sources": [...],
      "tags": ["AI", "Tech"],
      "images": [...]
    },
    "meta": {
      "tokens_used": 456,
      "latency_ms": 280,
      "cached": true
    }
  }
}
```

### POST /getAnswer

Generate grounded, analytical answer with optional SSE streaming.

**Request (non-stream):**
```json
{
  "inputs": {
    "query": "What is X?",
    "url": "https://example.com/article",
    "prompt": "Custom prompt",
    "lang": "zh-tw"
  },
  "user": "uuid_user",
  "stream": false
}
```

**Request (stream):**
Same as above with `"stream": true`. Response is SSE stream with events:
- `workflow_started`
- `token_chunk`
- `citations`
- `workflow_finished`

**Response (non-stream):**
```json
{
  "event": "workflow_finished",
  "data": {
    "outputs": {
      "result": "Full answer text..."
    },
    "provider": "gemini-2.5-flash",
    "meta": {
      "tokens_used": 712,
      "latency_ms": 1200,
      "cached": false
    }
  }
}
```

## Architecture

```
app.py                    # FastAPI main application
├── services/
│   ├── gemini_service.py    # Gemini API integration
│   ├── search_service.py    # Google Search & web scraping
│   ├── cache_service.py     # Redis/file caching
│   └── content_service.py   # Content fetching
└── requirements.txt         # Python dependencies
```

## Caching

The server implements multi-tier caching:

1. **Redis** (primary) - Fast in-memory cache
2. **File system** (fallback) - When Redis is unavailable

**Cache TTLs:**
- Questions: 10 minutes
- Metadata: 1 hour
- Answers: 5 minutes

### Setting Up Redis

**Using Docker:**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Local Installation:**
- macOS: `brew install redis && brew services start redis`
- Ubuntu: `sudo apt-get install redis-server`

Then add to `.env`:
```env
REDIS_URL=redis://localhost:6379/0
```

## Deployment

### Development

```bash
python run.py
```

### Production with Uvicorn

```bash
uvicorn app:app --host 0.0.0.0 --port 8888 --workers 4
```

### Docker

**Build and run:**
```bash
docker build -t aigc-api-server .
docker run -p 8888:8888 --env-file .env aigc-api-server
```

**Using Docker Compose:**
```bash
docker-compose up -d
```

### Production Considerations

1. Use environment variables for all secrets
2. Configure proper CORS origins in `app.py`
3. Set up Redis for production caching
4. Use reverse proxy (nginx) for SSL termination
5. Monitor logs and metrics
6. Set up rate limiting
7. Use process manager (systemd, supervisor, etc.)

## Testing

### Quick Test Script

Run the automated test suite:

```bash
# Install requests if not already installed
pip install requests

# Run tests
python test_api.py
```

The test script will:
- Check server health
- Test all three endpoints
- Verify response formats
- Test both streaming and non-streaming modes
- Provide a detailed summary

### Manual Testing with curl

**Health Check:**
```bash
curl http://localhost:8888/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2025-01-29T..."}
```

**Generate Questions:**
```bash
curl -X POST http://localhost:8888/generateQuestions \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "url": "https://example.com/article",
      "lang": "zh-tw"
    },
    "user": "test_user"
  }'
```

**Get Metadata:**
```bash
curl -X POST http://localhost:8888/getMetadata \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "url": "https://example.com/article",
      "query": "test query"
    },
    "user": "test_user"
  }'
```

**Get Answer (Non-Streaming):**
```bash
curl -X POST http://localhost:8888/getAnswer \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "query": "What is this article about?",
      "url": "https://example.com/article",
      "lang": "zh-tw"
    },
    "user": "test_user",
    "stream": false
  }'
```

**Get Answer (Streaming - SSE):**
```bash
curl -X POST http://localhost:8888/getAnswer \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "query": "What is this article about?",
      "url": "https://example.com/article",
      "lang": "zh-tw"
    },
    "user": "test_user",
    "stream": true
  }'
```

### Testing with Python requests

You can also test programmatically:

```python
import requests

# Health check
response = requests.get("http://localhost:8888/health")
print(response.json())

# Generate questions
payload = {
    "inputs": {"url": "https://example.com", "lang": "zh-tw"},
    "user": "test_user"
}
response = requests.post("http://localhost:8888/generateQuestions", json=payload)
print(response.json())
```

### Using Postman or Insomnia

1. Import the endpoints:
   - `GET http://localhost:8888/health`
   - `POST http://localhost:8888/generateQuestions`
   - `POST http://localhost:8888/getMetadata`
   - `POST http://localhost:8888/getAnswer`

2. Set headers:
   - `Content-Type: application/json`

3. Add request bodies (JSON format) as shown in the API Endpoints section above.

## Troubleshooting

### Server won't start

- **Check Python version**: `python --version` (should be 3.11+)
- **Verify dependencies**: `python -c "import fastapi; import google.generativeai; print('OK')"`
- **Check port availability**: Ensure port 8888 is not in use

### API calls failing

- **Verify API key**: Check `.env` file contains valid `GEMINI_API_KEY`
- **Check server logs**: Look for error messages
- **Test health endpoint**: `curl http://localhost:8888/health`

### Slow responses

- **Enable Redis caching**: Add `REDIS_URL` to `.env`
- **Check Gemini API quota**: Verify you haven't exceeded limits
- **Review cache hit rates**: Check logs for cache statistics

### Response format errors

- **Verify API contract**: Ensure request format matches examples
- **Check Laravel integration**: Review `Laravel Integration` section above

## Error Handling

- Automatic retry with exponential backoff (3 attempts)
- Graceful degradation when services unavailable
- Detailed error logging
- HTTP status codes matching API contract

## License

MIT
