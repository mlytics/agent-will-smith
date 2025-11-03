# Quick Test Guide

## Project Structure

✅ **Core Application:**
- `app.py` - Main FastAPI application
- `run.py` - Server runner script
- `services/` - Service layer (Gemini, Search, Cache, Content)

✅ **Configuration:**
- `.env.example` - Environment variables template
- `requirements.txt` - Python dependencies

✅ **Testing:**
- `test_api.py` - Automated test suite
- `demo_mock_server.py` - Mock server for testing without API keys

✅ **Deployment:**
- `Dockerfile` - Docker image definition
- `docker-compose.yml` - Docker Compose setup

✅ **Documentation:**
- `README.md` - Complete documentation
- `postman_collection.json` - Postman collection

---

## Quick Test

### Option 1: Test with Real Server (Requires Gemini API Key)

1. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start server:**
   ```bash
   python run.py
   ```

4. **Test in another terminal:**
   ```bash
   python test_api.py
   ```

### Option 2: Test with Demo Server (No API Keys Needed)

1. **Start demo server:**
   ```bash
   python demo_mock_server.py
   ```

2. **Test in another terminal:**
   ```bash
   python test_api.py
   ```

The demo server returns sample responses perfect for testing and screenshots.

---

## Test Individual Endpoints

### Health Check
```bash
curl http://localhost:8888/health
```

### Generate Questions
```bash
curl -X POST http://localhost:8888/generateQuestions \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"url": "https://example.com/article", "lang": "zh-tw"}, "user": "test"}'
```

### Get Metadata
```bash
curl -X POST http://localhost:8888/getMetadata \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"url": "https://example.com/article"}, "user": "test"}'
```

### Get Answer
```bash
curl -X POST http://localhost:8888/getAnswer \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"query": "What is this about?", "url": "https://example.com/article"}, "user": "test", "stream": false}'
```

---

## Project Status

✅ **Completed:**
- All three API endpoints implemented
- Gemini integration working
- Caching (Redis + file fallback)
- Error handling with location restriction detection
- SSE streaming support
- Docker support
- Complete documentation

✅ **Ready for:**
- Testing
- Deployment
- Integration with Laravel

