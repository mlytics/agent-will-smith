# Agent-Will-Smith API Server

Python FastAPI server that replaces the Vext API with Google Gemini backend. Maintains full compatibility with existing Laravel client code.

**Model**: Gemini 2.5 Flash Lite ($0.1/$0.4 per 1M tokens) - Cost-optimized choice vs Vext ($1/$1)

## Features

- **Five Core Endpoints**: `POST /generateQuestions`, `POST /getMetadata`, `POST /getAnswer`, `POST /eeat`, `POST /summarize`
- **Gemini Integration**: Uses Google Gemini for LLM operations
- **E-E-A-T Assessment**: Analyze content quality (Experience, Expertise, Authoritativeness, Trust) based on Google's Search Quality Rater Guidelines
- **Multi-Language Support**: Generate questions and answers in multiple languages via optional `lang` parameter
- **Caching**: Multi-tier caching (Redis + file fallback)
- **Streaming**: Server-Sent Events (SSE) support for answers
- **API Compatibility**: Maintains exact request/response format from Vext API

## Prerequisites

- Python 3.11+ (3.11/3.12 recommended)
- **Google Gemini API key** (REQUIRED) - [Get one here](https://ai.google.dev/)
- Redis (optional - file cache used as fallback)

## Quick Start

### 1. Install Dependencies

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

### 2. Configure Environment

Create `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
# Required in protected environments
API_BEARER_TOKEN=change_me
ALLOWED_ORIGINS=https://your-allowed-origin.com
# Optional
GEMINI_MODEL=gemini-2.5-flash-lite  # Cost: $0.1/$0.4 per 1M tokens (input/output)
REDIS_URL=redis://localhost:6379/0
```

### 3. Run the Server

```bash
python run.py
```

Server starts on `http://localhost:8888`

### 4. Test

#### Quick Health Check
```bash
curl http://localhost:8888/health
```

#### Generate Questions (with URL)
```bash
curl -X POST http://localhost:8888/generateQuestions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "inputs": {
      "url": "https://m.cnyes.com/news/id/5627491",
      "lang": "zh-tw"
    },
    "user": "test_user",
    "type": "answer_page"
  }'
```

#### Generate Questions (with Context - Widget Page)
```bash
curl -X POST http://localhost:8888/generateQuestions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "inputs": {
      "url": "",
      "context": "A股港股《異動股》天泓文創(08500)升逾40%,現報0.75元...",
      "prompt": "# 角色 你是鉅亨網（Cnyes.com）的資深金融新聞記者，擅長以市場節奏與專業語氣撰寫能引起投資人關注的「提問式標題」。\n# 任務 根據提供的文章，生成一個「標題式提問」。",
      "lang": "zh-tw"
    },
    "user": "86b51fd1-5186-45c2-84f6-7977dd616119",
    "type": "widget_page",
    "source_url": "https://m.cnyes.com/news/id/5627491"
  }'
```

#### Get Metadata (with Domain Filtering)
```bash
curl -X POST http://localhost:8888/getMetadata \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "inputs": {
      "url": "https://m.cnyes.com/news/id/5627491",
      "query": "天泓文創 股票 異動",
      "tag_prompt": "Generate 5 concise topic tags"
    },
    "user": "test_user"
  }'
```

#### Get Answer (with URL)
```bash
curl -X POST http://localhost:8888/getAnswer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "inputs": {
      "query": "天泓文創股價為何飆升？",
      "url": "https://m.cnyes.com/news/id/5627491",
      "lang": "zh-tw"
    },
    "user": "test_user",
    "stream": false
  }'
```

#### Get Answer (with Content ID - Session)
```bash
# First, generate questions to get content_id
# Then use that content_id to get answer
curl -X POST http://localhost:8888/getAnswer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "inputs": {
      "query": "天泓文創股價為何飆升？",
      "content_id": "56e71457-c55d-4b13-bc8a-205cbdb42673",
      "lang": "zh-tw"
    },
    "user": "test_user",
    "stream": false
  }'
```

#### EEAT Assessment (with URL)
```bash
curl -X POST http://localhost:8888/eeat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "inputs": {
      "input_type": "url",
      "url": "https://www.bnext.com.tw/article/85031/nissan-2025-q3-financial-report-reveals-challenges-and-transformation-strategies",
      "metadata": {
        "author": "John Doe",
        "publish_date": "2025-01-15",
        "topic_category": "financial"
      }
    },
    "user": "test_user"
  }'
```

#### EEAT Assessment (with Content)
```bash
curl -X POST http://localhost:8888/eeat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "inputs": {
      "input_type": "content",
      "content": "This is a comprehensive article about artificial intelligence and its applications in modern business. The author has over 10 years of experience in AI research and development.",
      "metadata": {
        "author": "Dr. Jane Smith",
        "publish_date": "2025-01-15",
        "topic_category": "technical"
      }
    },
    "user": "test_user"
  }'
```

#### Summarize Article (for Intent Engine)
```bash
curl -X POST http://localhost:8888/summarize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "title": "天泓文創(08500)盤中飆升逾40% 創52周新高",
    "content": "天泓文創(08500)今日盤中股價大幅上揚，最高見0.75元，升幅超過40%，創下52周新高。該股成交量明顯放大，主動買沽比率為55:45，顯示市場資金積極流入。技術指標方面，RSI相對強弱指標飆升至83.58，顯示股價已進入超買區間。分析師指出，此次股價異動可能與公司近期業務發展或市場傳聞有關，投資者需留意後續動向。",
    "author": "鉅亨網記者",
    "publish_time": "2025-11-20T10:30:00Z",
    "keywords": ["港股", "異動股", "天泓文創", "股票", "金融"],
    "category": "金融",
    "permalink": "https://m.cnyes.com/news/id/5627491"
  }'
```

#### Run Automated Tests
```bash
# Install test dependencies (if using uv)
uv sync --extra test

# Run all tests (uses default test domain: https://m.cnyes.com/news/id/5627491)
# With uv:
uv run pytest tests/ -v
# Or without uv:
pytest tests/ -v

# Run with custom test domain
TEST_DOMAIN=https://your-test-domain.com/article pytest tests/ -v

# Run specific test file
pytest tests/test_output_format.py -v

# Run with coverage
pytest tests/ -v --cov=app --cov=services
```

**Test Configuration:**
- `TEST_DOMAIN`: Test URL for API endpoints (default: `https://m.cnyes.com/news/id/5627491`)
- `TEST_BASE_URL`: Base URL for domain extraction tests (default: `https://m.cnyes.com`)

Set these in your `.env` file or export as environment variables before running tests.

## Configuration

Edit `.env` file:

```env
# Required
GEMINI_API_KEY=your_key_here
API_BEARER_TOKEN=change_me
ALLOWED_ORIGINS=https://your-allowed-origin.com

# Optional
GEMINI_MODEL=gemini-2.5-flash-lite  # Cost: $0.1/$0.4 per 1M tokens (input/output). Alternative: gemini-2.5-flash ($0.3/$2.5)
REDIS_URL=redis://localhost:6379/0
HOST=0.0.0.0
PORT=8888
LOG_LEVEL=INFO

# Google Custom Search (optional - only for related sources)
GOOGLE_SEARCH_KEY=
GOOGLE_SEARCH_ENGINE_ID=

# Test Configuration (optional - for running tests)
TEST_DOMAIN=https://m.cnyes.com/news/id/5627491
TEST_BASE_URL=https://m.cnyes.com
```

## Security

- **Bearer token authentication**: All POST endpoints require `Authorization: Bearer <token>`. Configure the shared secret via `API_BEARER_TOKEN`. When the variable is unset (local development), authentication is skipped but a warning is logged.
- **CORS policy**: Control allowed origins with the comma-separated `ALLOWED_ORIGINS` variable. If omitted, only localhost origins are allowed.
- Store secrets with your deployment platform's secret manager (for example, Cloud Run secrets) and rotate them regularly.

## Go-Live Decisions

**Model Choice**: Gemini 2.5 Flash Lite ($0.1/$0.4 per 1M tokens) - Cost-optimized vs Vext ($1/$1). Databricks AI Gateway kept on roadmap for future A/B testing.

**Authentication**: Bearer token authentication implemented. Firewall setup skipped for Cloud Run (too tedious).

**Scaling**: Cloud Run auto-scaling configured (max 10 instances). Bottleneck expected to be Gemini response latency.

**Observability**: Cloud Run dashboard provides basic metrics and logs. Additional monitoring can be added as needed.

**Testing**: 
- **Automated tests**: Comprehensive unit and API tests covering schema validation, input/output format, URL/context precedence, and content_id session logic. Run with `pytest tests/ -v`
- **Manual testing**: Postman collection available for E2E testing after deployment
- **Human evaluation**: Content quality evaluation by team members

## Laravel Integration

Update `MyLib/MyAPI.php`:

```php
// Change from:
private $api_host = "https://mlytics-api.vextapp.com";

// To:
private $api_host = "https://your-api-server.com";
```

**That's it!** The API contract is identical. All existing Laravel code works without modifications.

## API Endpoints

### POST /generateQuestions

Generate 1-5 questions from content or URL.

**Request:**
```json
{
  "inputs": {
    "url": "https://m.cnyes.com/news/id/5627491",
    "context": "Optional: direct content text",
    "prompt": "Optional: custom prompt for question generation",
    "lang": "zh-tw",
    "previous_questions": ["Optional: list of previous questions"]
  },
  "user": "86b51fd1-5186-45c2-84f6-7977dd616119",
  "type": "widget_page",
  "source_url": "https://m.cnyes.com/news/id/5627491"
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
        "question_1": "天泓文創(08500)盤中飆升逾40%，創52周新高，背後有何催化劑？",
        "question_2": "天泓文創股價放量創高，市場資金動向透露了什麼訊號？",
        "question_3": "成交量與股價同步走高，這是否意味著天泓文創的上升趨勢將持續？",
        "question_4": "55:45的主動買沽比率，如何解讀市場對天泓文創的看法？",
        "question_5": "RSI飆升至83.58，天泓文創是否已進入超買區間？"
      },
      "content_id": "56e71457-c55d-4b13-bc8a-205cbdb42673"
    },
    "elapsed_time": 1.605955,
    "created_at": 1761248073,
    "finished_at": 1761248075
  }
}
```

**Note:** If both `url` and `context` are provided, `context` takes precedence. Empty string `url: ""` is treated as no URL.

**Language Parameter (`lang`):**
- Optional parameter (defaults to `"zh-tw"` if not specified)
- Controls the language of generated questions
- See [Language Support](#language-support) section for supported language codes

### POST /getMetadata

Extract metadata (title, summary, tags, images) from URL. **Domain filtering:** Search results are automatically filtered to only include items from the same domain as the input URL.

**Request:**
```json
{
  "inputs": {
    "url": "https://m.cnyes.com/news/id/5627491",
    "query": "天泓文創 股票 異動",
    "tag_prompt": "Generate 5 concise topic tags"
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
      "tag": "港股, 異動股, 天泓文創, 股票, 金融",
      "images": [
        {
          "images": "{\n  \"images\": []\n}"
        }
      ],
      "sources": [
        {
          "sources": "{\n  \"citations\": [\n    {\n      \"title\": \"相關文章標題\",\n      \"url\": \"https://cnyes.com/related-article\",\n      \"content\": \"相關文章摘要...\"\n    }\n  ]\n}"
        }
      ]
    },
    "elapsed_time": 2.41,
    "created_at": 1761245271,
    "finished_at": 1761245273
  }
}
```

**Note:** Domain is normalized (e.g., `m.cnyes.com` → `cnyes.com`). All sources are filtered to match the extracted domain.

### POST /getAnswer

Generate answer with optional SSE streaming. Can use `content_id` from `/generateQuestions` to retrieve previously saved content.

**Request:**
```json
{
  "inputs": {
    "query": "天泓文創股價為何飆升？",
    "url": "https://m.cnyes.com/news/id/5627491",
    "content_id": "56e71457-c55d-4b13-bc8a-205cbdb42673",
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
      "citations": [
        {
          "title": "4beb171d-1d30-498c-af57-45763c314903",
          "url": "4beb171d-1d30-498c-af57-45763c314903",
          "content_id": "4beb171d-1d30-498c-af57-45763c314903",
          "author": null,
          "publish_time": null,
          "thumbnail_url": null
        }
      ],
      "citation_type": "cached"
    },
    "elapsed_time": 3.709378,
    "created_at": 1761248666,
    "finished_at": 1761248670
  }
}
```

**Response (streaming - final event):**
The streaming response sends SSE events (`workflow_started`, `token_chunk`, `citations`, `workflow_finished`). The final `workflow_finished` event matches the non-streaming format above.

**Note:** If `content_id` is provided, it retrieves content saved during `/generateQuestions` and includes it in citations with `citation_type: "cached"`. Otherwise, it fetches from `url`. Set `"stream": true` for SSE streaming.

**Error Handling:**
- If `content_id` is provided but not found or expired (content expires after 10 minutes from `/generateQuestions`), the API returns `"status": "failed"` with empty `outputs: {}`
- If both `url` and `content_id` are empty, the API returns `"status": "failed"` with empty `outputs: {}`
- This matches Vext API behavior for consistency
- **Note:** `content_id` from `/generateQuestions` is valid for 10 minutes. After that, use the `url` parameter or regenerate questions to get a new `content_id`

**Response (failed status):**
```json
{
  "event": "workflow_finished",
  "task_id": "fedb98f1-fb3e-4a0f-bde2-3aeaedf1b10c",
  "data": {
    "status": "failed",
    "outputs": {},
    "elapsed_time": 1.655961,
    "created_at": 1763691378,
    "finished_at": 1763691379
  }
}
```

**Language Parameter (`lang`):**
- Optional parameter (defaults to `"zh-tw"` if not specified)
- Controls the language of generated answers
- Works for both streaming and non-streaming responses
- See [Language Support](#language-support) section for supported language codes

### POST /eeat (or /api/v1/content/eeat-assessment)

Assess E-E-A-T (Experience, Expertise, Authoritativeness, Trust) quality of content based on Google's Search Quality Rater Guidelines.

**Request:**
```json
{
  "inputs": {
    "input_type": "url",
    "url": "https://example.com/article",
    "content": "Optional: direct content text (if input_type is 'content')",
    "metadata": {
      "author": "Optional: author name",
      "publish_date": "Optional: YYYY-MM-DD format",
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
      "experience": {
        "level": "High",
        "confidence": 0.85,
        "rationale": [
          "Author demonstrates first-hand usage of the product reviewed",
          "Includes personal anecdotes and specific details from direct interaction",
          "Photos and videos suggest authentic personal experience"
        ]
      },
      "expertise": {
        "level": "High",
        "confidence": 0.78,
        "rationale": [
          "Author holds relevant credentials in the field",
          "Content demonstrates deep technical knowledge",
          "Explanations show nuanced understanding of complex topics"
        ]
      },
      "authoritativeness": {
        "level": "High",
        "confidence": 0.92,
        "rationale": [
          "Published on recognized authoritative website in this domain",
          "Author cited by other reputable sources in the field",
          "Content referenced in academic or professional contexts"
        ]
      },
      "trust": {
        "level": "Trustworthy",
        "confidence": 0.88,
        "rationale": [
          "No evidence of inaccurate or misleading information",
          "Clear disclosure of affiliations and potential conflicts",
          "Contact information and customer service details readily available"
        ]
      }
    },
    "page_quality_rating": "High",
    "is_ymyl": true,
    "evidence_summary": {
      "on_page": [
        "Clear author bio with credentials",
        "Transparent about content purpose",
        "Well-structured and informative main content"
      ],
      "external": [
        "Positive reviews from independent sources found",
        "Author has established professional presence",
        "No significant controversies or trust issues detected"
      ]
    },
    "recommendations": [
      "Consider adding more specific examples from personal experience",
      "Include citations to support key factual claims",
      "Add more detailed author credentials visible on page"
    ]
  },
  "metadata": {
    "analyzed_at": "2025-11-15T10:30:00Z",
    "processing_time_ms": 2340,
    "content_length": 2500,
    "language": "en"
  }
}
```

**E-E-A-T Level Definitions:**
- **Experience**: `High` | `Adequate` | `Lacking` | `N/A`
- **Expertise**: `High` | `Adequate` | `Lacking` | `N/A`
- **Authoritativeness**: `Very High` | `High` | `Adequate` | `Lacking` | `N/A`
- **Trust**: `Trustworthy` | `Adequate` | `Untrustworthy`
- **Page Quality**: `Highest` | `High` | `Medium` | `Low` | `Lowest`

**Notes:**
- Use `input_type: "url"` to analyze content from a URL, or `input_type: "content"` for direct text
- If Trust is `Untrustworthy`, overall rating is automatically set to `Lowest`
- Metadata is optional but helps improve assessment accuracy
- Results are cached for 1 hour
- Both `/eeat` and `/api/v1/content/eeat-assessment` endpoints are available

### POST /summarize

Generate comprehensive summaries for Intent Engine content_article table. This endpoint is designed for Databricks integration to populate summary fields in the Intent Engine.

**Request:**
```json
{
  "title": "Article title",
  "content": "Full article content text...",
  "author": "Optional: author name",
  "publish_time": "Optional: ISO 8601 timestamp (e.g., 2025-11-20T10:30:00Z)",
  "keywords": ["Optional", "array", "of", "keywords"],
  "category": "Optional: category name",
  "permalink": "Optional: article URL"
}
```

**Response:**
```json
{
  "full_summary": "Comprehensive 2-3 paragraph summary of the article covering main points, key insights, and conclusions.",
  "bullet_summary": [
    "Key point 1",
    "Key point 2",
    "Key point 3",
    "Key point 4",
    "Key point 5"
  ],
  "semantic_paragraphs": {
    "paragraphs": [
      {
        "text": "Introduction paragraph text...",
        "semantic_role": "introduction"
      },
      {
        "text": "Main body paragraph text...",
        "semantic_role": "body"
      },
      {
        "text": "Conclusion paragraph text...",
        "semantic_role": "conclusion"
      }
    ]
  },
  "entities": {
    "persons": ["Person Name 1", "Person Name 2"],
    "organizations": ["Organization 1", "Organization 2"],
    "locations": ["Location 1", "Location 2"],
    "products": ["Product 1"],
    "events": ["Event 1"]
  },
  "labels": {
    "topics": ["topic1", "topic2", "topic3"],
    "sentiment": "positive",
    "category": "金融",
    "content_type": "news"
  }
}
```

**Notes:**
- `title` and `content` are required fields
- All other fields are optional but help improve summarization quality
- Results are cached for 1 hour based on content hash
- Designed for batch processing from Databricks Intent Engine pipeline
- Returns structured JSON suitable for direct database updates

## Language Support

The API supports generating questions and answers in multiple languages through the optional `lang` parameter in both `/generateQuestions` and `/getAnswer` endpoints.

### Supported Language Codes

| Code | Language | Native Name |
|------|----------|-------------|
| `en` | English | English |
| `zh-tw` | Traditional Chinese | 繁體中文 (default) |
| `zh-cn` | Simplified Chinese | 简体中文 |
| `zh` | Chinese (generic) | 中文 |
| `es` | Spanish | Español |
| `fr` | French | Français |
| `de` | German | Deutsch |
| `it` | Italian | Italiano |
| `pt` | Portuguese | Português |
| `ja` | Japanese | 日本語 |
| `ko` | Korean | 한국어 |
| `ru` | Russian | Русский |
| `ar` | Arabic | العربية |
| `hi` | Hindi | हिन्दी |
| `th` | Thai | ไทย |
| `vi` | Vietnamese | Tiếng Việt |
| `id` | Indonesian | Bahasa Indonesia |
| `nl` | Dutch | Nederlands |
| `pl` | Polish | Polski |
| `tr` | Turkish | Türkçe |

### Usage Examples

#### Generate Questions in English
```bash
curl -X POST http://localhost:8888/generateQuestions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "inputs": {
      "url": "https://example.com/article",
      "lang": "en"
    },
    "user": "test_user",
    "type": "answer_page"
  }'
```

#### Generate Questions in Japanese
```bash
curl -X POST http://localhost:8888/generateQuestions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "inputs": {
      "url": "https://example.com/article",
      "lang": "ja"
    },
    "user": "test_user",
    "type": "answer_page"
  }'
```

#### Get Answer in Spanish
```bash
curl -X POST http://localhost:8888/getAnswer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer change_me" \
  -d '{
    "inputs": {
      "query": "What are the key benefits?",
      "url": "https://example.com/article",
      "lang": "es"
    },
    "user": "test_user",
    "stream": false
  }'
```

**Note:** If the `lang` parameter is omitted, the API defaults to `"zh-tw"` (Traditional Chinese). The language code is case-insensitive and will be normalized automatically.

## Caching

- **Redis** (primary) - Fast in-memory cache
- **File system** (fallback) - Automatic when Redis unavailable

**Setup Redis (Optional):**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

Add to `.env`: `REDIS_URL=redis://localhost:6379/0`

## Deployment

**Development:**
```bash
python run.py
```

**Production:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8888 --workers 4
```

**Docker:**
```bash
docker build -t aigc-api-server .
docker run -p 8888:8888 --env-file .env aigc-api-server
```



## Troubleshooting

### Installation Issues

- **Python 3.13 Rust errors**: Use pre-built wheels or use Python 3.11/3.12
- **Missing modules**: `uv sync` (or `pip install -e .` if not using uv)

### Connection Issues

- **API key invalid**: Check `.env` file contains correct `GEMINI_API_KEY`
- **Connection timeout**: Check firewall, VPN, or network restrictions
- **Redis not working**: File cache will be used automatically (no action needed)

### Server Issues

- **Port in use**: Change `PORT` in `.env` or kill process using port 8888
- **Import errors**: Verify all dependencies installed: `uv sync` (or `pip install -e .` if not using uv)

## Project Structure

```
app.py                    # FastAPI main application
├── services/
│   ├── gemini_service.py    # Gemini API integration
│   ├── search_service.py    # Google Search & web scraping
│   ├── cache_service.py     # Redis/file caching
│   └── content_service.py   # Content fetching
└── pyproject.toml          # Python dependencies (uv/pip)
```

## License

MIT
