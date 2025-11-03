#!/usr/bin/env python3
"""
Mock API Server for Demo/Presentation
Works without API keys - returns sample responses
Perfect for screenshots and demonstrations
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
from datetime import datetime

app = FastAPI(title="AIGC MVP API - Demo Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Request Models
class GenerateQuestionsInput(BaseModel):
    url: Optional[str] = None
    context: Optional[str] = None
    lang: Optional[str] = "zh-tw"
    previous_questions: Optional[list] = []

class GenerateQuestionsRequest(BaseModel):
    inputs: GenerateQuestionsInput
    user: str = "uuid_user"
    type: Optional[str] = "answer_page"

class GetMetadataInput(BaseModel):
    query: Optional[str] = ""
    url: Optional[str] = None
    tag_prompt: Optional[str] = ""

class GetMetadataRequest(BaseModel):
    inputs: GetMetadataInput
    user: str = "uuid_user"

class GetAnswerInput(BaseModel):
    query: str = ""
    url: Optional[str] = ""
    prompt: Optional[str] = ""
    content_id: Optional[str] = ""
    lang: Optional[str] = "zh-tw"

class GetAnswerRequest(BaseModel):
    inputs: GetAnswerInput
    user: str = "uuid_user"
    stream: Optional[bool] = False

# Demo Responses
DEMO_QUESTIONS_RESPONSE = {
    "event": "workflow_finished",
    "data": {
        "outputs": {
            "result": [
                {
                    "id": "q1",
                    "text": "What are the key benefits of artificial intelligence in modern business?",
                    "type": "analytical",
                    "confidence": 0.95
                },
                {
                    "id": "q2",
                    "text": "How does machine learning differ from traditional programming?",
                    "type": "factual",
                    "confidence": 0.92
                },
                {
                    "id": "q3",
                    "text": "What are the potential challenges in implementing AI solutions?",
                    "type": "exploratory",
                    "confidence": 0.88
                },
                {
                    "id": "q4",
                    "text": "How can companies prepare for AI transformation?",
                    "type": "analytical",
                    "confidence": 0.90
                },
                {
                    "id": "q5",
                    "text": "What are the latest trends in AI technology?",
                    "type": "exploratory",
                    "confidence": 0.87
                }
            ],
            "content_id": "demo-content-123"
        },
        "provider": "gemini-2.5-flash-lite",
        "meta": {
            "tokens_used": 342,
            "latency_ms": 520,
            "cached": False
        }
    }
}

DEMO_METADATA_RESPONSE = {
    "event": "workflow_finished",
    "data": {
        "outputs": {
            "url": "https://example.com/article",
            "domain": "example.com",
            "title": "The Future of Artificial Intelligence in Business",
            "summary": "A comprehensive analysis of how AI is transforming modern business operations and strategies.",
            "sources": [
                {
                    "title": "AI in Business: A Complete Guide",
                    "url": "https://related-source-1.com",
                    "snippet": "How artificial intelligence is revolutionizing business processes...",
                    "score": 0.9
                },
                {
                    "title": "Machine Learning for Enterprises",
                    "url": "https://related-source-2.com",
                    "snippet": "Enterprise adoption of ML technologies is growing rapidly...",
                    "score": 0.8
                }
            ],
            "tags": ["Artificial Intelligence", "Business", "Technology", "Machine Learning", "Innovation"],
            "images": [
                {
                    "url": "https://example.com/images/ai-business.jpg",
                    "width": 1200,
                    "height": 800
                }
            ]
        },
        "provider": "gemini-2.5-flash",
        "meta": {
            "tokens_used": 567,
            "latency_ms": 380,
            "cached": False,
            "search_api_quota_used": 1
        }
    }
}

DEMO_ANSWER_RESPONSE = {
    "event": "workflow_finished",
    "data": {
        "outputs": {
            "result": """Artificial intelligence is transforming modern business in several key ways:

**1. Automation and Efficiency**
AI enables businesses to automate repetitive tasks, reducing operational costs and increasing efficiency. Companies can process large volumes of data quickly and accurately.

**2. Data-Driven Decision Making**
AI algorithms analyze vast amounts of data to provide insights that help executives make informed decisions. This leads to better strategic planning and resource allocation.

**3. Customer Experience Enhancement**
AI-powered chatbots and recommendation systems provide personalized customer experiences, improving satisfaction and retention rates.

**4. Predictive Analytics**
Machine learning models can predict market trends, customer behavior, and potential risks, allowing businesses to stay ahead of the competition.

**5. Innovation and Competitive Advantage**
Companies that successfully implement AI gain significant competitive advantages through improved products, services, and operational excellence."""
        },
        "provider": "gemini-2.5-flash",
        "meta": {
            "tokens_used": 485,
            "latency_ms": 1120,
            "cached": False
        }
    }
}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "mode": "demo"}

@app.post("/generateQuestions")
async def generate_questions(request: GenerateQuestionsRequest):
    """Demo endpoint - returns sample questions"""
    return JSONResponse(content=DEMO_QUESTIONS_RESPONSE)

@app.post("/getMetadata")
async def get_metadata(request: GetMetadataRequest):
    """Demo endpoint - returns sample metadata"""
    # Customize response based on request
    response = DEMO_METADATA_RESPONSE.copy()
    if request.inputs.url:
        response["data"]["outputs"]["url"] = request.inputs.url
        response["data"]["outputs"]["domain"] = request.inputs.url.split("/")[2] if "//" in request.inputs.url else "example.com"
    return JSONResponse(content=response)

@app.post("/getAnswer")
async def get_answer(request: GetAnswerRequest):
    """Demo endpoint - returns sample answer"""
    response = DEMO_ANSWER_RESPONSE.copy()
    # Customize answer based on query
    if request.inputs.query:
        response["data"]["outputs"]["result"] = f"""Based on your question: "{request.inputs.query}"

Here is a comprehensive answer generated using AI analysis:

The question you asked addresses important aspects of modern technology and business. This response demonstrates how the system can:
- Analyze content and questions
- Provide detailed, well-structured answers
- Support multiple languages
- Return responses in real-time

**Key Points:**
1. Accurate analysis of the content
2. Clear and structured response
3. Relevant examples and explanations
4. Professional formatting

This demonstrates the full capabilities of the AI-powered answer generation system."""
    return JSONResponse(content=response)

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  DEMO MODE - Mock API Server")
    print("  No API keys required!")
    print("="*60)
    print("\nServer starting on http://localhost:8888")
    print("Perfect for screenshots and demonstrations\n")
    uvicorn.run(app, host="0.0.0.0", port=8888)

