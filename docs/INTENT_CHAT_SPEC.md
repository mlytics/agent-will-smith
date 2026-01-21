# Intent-Driven Chat Experience 整合規格書 v2.0

## 基於 User Journey 的完整實作規格

---

## 目錄
1. [專案概述](#1-專案概述)
2. 2. [系統架構](#2-系統架構)
   3. 3. [Chat Agent 設計](#3-chat-agent-設計)
      4. 4. [API 規格](#4-api-規格)
         5. 5. [前端實作規格](#5-前端實作規格)
            6. 6. [UI 元件設計](#6-ui-元件設計)
               7. 7. [實作流程](#7-實作流程)
                 
                  8. ---
                 
                  9. ## 1. 專案概述
                 
                  10. ### 1.1 User Journey 對應
                 
                  11. | Stage | 用戶狀態 | 系統行為 | Mlytics 介入程度 |
                  12. |-------|---------|---------|-----------------|
                  13. | **Discovery** | 被動閱讀 | 文章內嵌 AIGC Widget | 開始介入 |
                  14. | **Engagement** | 主動提問 | 顯示 Quick Question Chips + 開啟對話 | 深度介入 |
                  15. | **Intent Qualification** | 探索解決方案 | 透過對話捕捉 intent signals | 深度介入 |
                  16. | **Conversion Bridge** | 考慮購買 | 呈現產品推薦卡片 | 變現點 |
                 
                  17. ### 1.2 核心設計原則
                 
                  18. 1. **Reuse 現有 product_recommendation** — 不修改 `agent-will-smith` 中 article 相關邏輯
                      2. 2. **Chat Agent 作為 Orchestrator** — 新增 Chat Agent 負責對話、意圖捕捉，並將 `product_recommendation` 當作 Tool 調用
                         3. 3. **Intent 漸進式收集** — 透過對話累積 Intent Profile，時機成熟才觸發產品推薦
                           
                            4. ### 1.3 現有元件 Reuse 策略
                           
                            5. ```
                               ┌─────────────────────────────────────────────────────────────────┐
                               │                     新增: Chat Agent                            │
                               │  (負責對話管理、意圖捕捉、決定何時調用 tools)                      │
                               └───────────────────────────┬─────────────────────────────────────┘
                                                           │ Tool Call
                                                           ▼
                               ┌─────────────────────────────────────────────────────────────────┐
                               │           現有: product_recommendation Agent (不修改)            │
                               │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
                               │  │ IntentNode  │→ │ SearchNode  │→ │     OutputNode          │  │
                               │  │ (分析文章)   │  │ (向量搜尋)   │  │ (組裝產品結果)           │  │
                               │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
                               └─────────────────────────────────────────────────────────────────┘
                               ```

                               ---

                               ## 2. 系統架構

                               ### 2.1 整體架構

                               ```
                               ┌─────────────────────────────────────────────────────────────────────┐
                               │                        Frontend (Next.js)                           │
                               │  ┌───────────────────────────────────────────────────────────────┐  │
                               │  │                      assistant-ui                              │  │
                               │  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐  │  │
                               │  │  │ QuickChips  │  │   Thread    │  │  Tool UIs             │  │  │
                               │  │  │ (初始推薦)   │  │ (對話介面)  │  │  • ProductCard        │  │  │
                               │  │  │             │  │             │  │  • IntentConfirm      │  │  │
                               │  │  │             │  │             │  │  • RiskPreference     │  │  │
                               │  │  └─────────────┘  └─────────────┘  └───────────────────────┘  │  │
                               │  └───────────────────────────────────────────────────────────────┘  │
                               └───────────────────────────────┬─────────────────────────────────────┘
                                                               │ SSE Streaming
                                                               ▼
                               ┌─────────────────────────────────────────────────────────────────────┐
                               │                    Backend (agent-will-smith)                        │
                               │                                                                      │
                               │  ┌────────────────────────────────────────────────────────────────┐ │
                               │  │               【新增】Chat Agent (Orchestrator)                  │ │
                               │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │ │
                               │  │  │ Conversation│→ │ Intent      │→ │   Tool Selection        │ │ │
                               │  │  │ Node        │  │ Tracker     │  │   & Invocation          │ │ │
                               │  │  └─────────────┘  └─────────────┘  └──────────┬──────────────┘ │ │
                               │  └───────────────────────────────────────────────┼────────────────┘ │
                               │                                                  │                   │
                               │                         ┌────────────────────────┼──────────────┐   │
                               │                         │        Available Tools               │   │
                               │                         │  ┌──────────────────────────────────┐│   │
                               │                         │  │ tool: get_product_recommendations ││   │
                               │                         │  │ (wraps existing Agent.invoke())   ││   │
                               │                         │  └──────────────────────────────────┘│   │
                               │                         │  ┌──────────────────────────────────┐│   │
                               │                         │  │ tool: ask_clarification          ││   │
                               │                         │  │ (觸發 UI 選項讓用戶選擇)           ││   │
                               │                         │  └──────────────────────────────────┘│   │
                               │                         │  ┌──────────────────────────────────┐│   │
                               │                         │  │ tool: capture_intent_signal      ││   │
                               │                         │  │ (記錄用戶透露的資訊)               ││   │
                               │                         │  └──────────────────────────────────┘│   │
                               │                         └───────────────────────────────────────┘   │
                               │                                                                      │
                               │  ┌────────────────────────────────────────────────────────────────┐ │
                               │  │            【現有】product_recommendation Agent                  │ │
                               │  │            (完全不修改，透過 invoke() 被 tool 調用)               │ │
                               │  └────────────────────────────────────────────────────────────────┘ │
                               └─────────────────────────────────────────────────────────────────────┘
                               ```

                               ---

                               ## 3. Chat Agent 設計

                               ### 3.1 新增 Chat Agent 結構

                               ```
                               src/agent_will_smith/agent/
                               ├── product_recommendation/     # 【現有，不修改】
                               │   ├── agent.py
                               │   ├── config.py
                               │   ├── container.py
                               │   ├── state.py
                               │   ├── model/
                               │   ├── node/
                               │   └── repo/
                               │
                               └── intent_chat/                # 【新增】
                                   ├── __init__.py
                                   ├── agent.py               # Chat Agent 主邏輯
                                   ├── config.py              # Chat Agent 配置
                                   ├── container.py           # DI Container
                                   ├── state.py               # Chat State (含 Intent Profile)
                                   ├── tools/                 # Tools 定義
                                   │   ├── __init__.py
                                   │   ├── product_recommendation_tool.py  # 封裝現有 Agent
                                   │   ├── clarification_tool.py           # 確認意圖
                                   │   └── intent_capture_tool.py          # 記錄 signal
                                   └── prompts/
                                       └── system_prompt.py   # Chat Agent 系統提示詞
                               ```

                               ### 3.2 Chat State 設計

                               ```python
                               # agent/intent_chat/state.py

                               from typing import Literal, Optional
                               from pydantic import BaseModel, Field
                               from datetime import datetime

                               class IntentSignal(BaseModel):
                                   """單一意圖信號"""
                                   signal_type: str  # e.g., "life_stage", "asset_range", "risk_preference"
                                   value: str
                                   confidence: float = Field(ge=0, le=1)
                                   captured_at: datetime = Field(default_factory=datetime.now)
                                   source: str  # "user_input", "inferred", "explicit_selection"

                               class IntentProfile(BaseModel):
                                   """累積的用戶意圖檔案"""
                                   life_stage: Optional[str] = None           # "pre-retirement", "young_professional"
                                   age_estimate: Optional[str] = None         # "55-60", "30-35"
                                   asset_range: Optional[str] = None          # "3M-5M TWD", "under 1M"
                                   risk_preference: Optional[str] = None      # "conservative", "moderate", "aggressive"
                                   product_interests: list[str] = Field(default_factory=list)
                                   pain_points: list[str] = Field(default_factory=list)
                                   intent_score: int = Field(default=0, ge=0, le=100)
                                   purchase_timeline: Optional[str] = None    # "immediate", "3-6 months", "exploring"
                                   signals: list[IntentSignal] = Field(default_factory=list)

                               class ChatMessage(BaseModel):
                                   """對話訊息"""
                                   role: Literal["user", "assistant", "system"]
                                   content: str
                                   tool_calls: Optional[list[dict]] = None
                                   tool_results: Optional[list[dict]] = None
                                   timestamp: datetime = Field(default_factory=datetime.now)

                               class ChatInput(BaseModel):
                                   """Chat Agent 輸入"""
                                   message: str
                                   context: Optional[str] = None  # 文章內容（如果是從文章頁進入）
                                   session_id: str
                                   source_article_id: Optional[str] = None
                                   source_url: Optional[str] = None

                               class ChatOutput(BaseModel):
                                   """Chat Agent 輸出"""
                                   message: str
                                   tool_calls: list[dict] = Field(default_factory=list)
                                   intent_profile: IntentProfile
                                   suggested_actions: list[str] = Field(default_factory=list)
                                   should_recommend: bool = False

                               class ChatState(BaseModel):
                                   """完整對話狀態"""
                                   input: ChatInput
                                   messages: list[ChatMessage] = Field(default_factory=list)
                                   intent_profile: IntentProfile = Field(default_factory=IntentProfile)
                                   article_context: Optional[str] = None
                                   article_summary: Optional[str] = None
                                   output: Optional[ChatOutput] = None
                               ```

                               ### 3.3 Product Recommendation Tool (封裝現有 Agent)

                               ```python
                               # agent/intent_chat/tools/product_recommendation_tool.py

                               from langchain_core.tools import tool
                               from agent_will_smith.agent.product_recommendation.agent import Agent
                               from agent_will_smith.agent.product_recommendation.state import AgentInput

                               @tool
                               async def get_product_recommendations(
                                   context: str,
                                   question: str,
                                   verticals: list[str] = ["books", "travel", "activities"],
                                   k: int = 5,
                               ) -> dict:
                                   """
                                   根據對話上下文和用戶問題，推薦相關產品。
                                   只有當用戶的意圖已經足夠明確（intent_score >= 70）且適合推薦產品時才調用。

                                   Args:
                                       context: 對話上下文，包含文章內容和之前的對話摘要
                                       question: 基於 intent profile 組合的搜尋問題
                                       verticals: 要搜尋的產品類型
                                       k: 每個 vertical 返回的產品數量

                                   Returns:
                                       產品推薦結果
                                   """
                                   from agent_will_smith.agent.intent_chat.container import IntentChatContainer

                                   container = IntentChatContainer()
                                   product_agent = container.product_recommendation_agent()

                                   input_dto = AgentInput(
                                       article=context,
                                       question=question,
                                       verticals=verticals,
                                       k=k,
                                   )

                                   result = await product_agent.invoke(input_dto)

                                   return {
                                       "type": "product_recommendation",
                                       "grouped_results": result.grouped_results,
                                       "total_products": result.total_products,
                                       "intent": result.intent,
                                       "status": result.status,
                                   }
                               ```

                               ### 3.4 Clarification Tool

                               ```python
                               # agent/intent_chat/tools/clarification_tool.py

                               from langchain_core.tools import tool
                               from typing import Literal

                               @tool
                               def ask_clarification(
                                   question: str,
                                   options: list[dict],
                                   clarification_type: Literal["risk_preference", "timeline", "budget", "custom"]
                               ) -> dict:
                                   """
                                   向用戶提出選擇題來確認意圖。會在前端顯示為可點擊的選項按鈕。

                                   Args:
                                       question: 要問用戶的問題
                                       options: 選項列表，每個選項包含 {label: str, value: str}
                                       clarification_type: 問題類型
                                   """
                                   return {
                                       "type": "clarification_request",
                                       "question": question,
                                       "options": options,
                                       "clarification_type": clarification_type,
                                   }
                               ```

                               ---

                               ## 4. API 規格

                               ### 4.1 Chat Endpoint

                               **Endpoint:** `POST /api/v1/chat`

                               **Request:**
                               ```typescript
                               interface ChatRequest {
                                 message: string;
                                 session_id: string;
                                 context?: {
                                   article_content?: string;
                                   article_id?: string;
                                   source_url?: string;
                                   publisher?: string;
                                 };
                                 intent_profile?: IntentProfile;
                               }
                               ```

                               **Response (SSE Stream):**
                               ```typescript
                               // 文字回應
                               data: {"type": "text-delta", "textDelta": "了解..."}

                               // 選項問題
                               data: {
                                 "type": "tool-call",
                                 "toolCallId": "call_abc",
                                 "toolName": "ask_clarification",
                                 "args": {
                                   "question": "您比較傾向哪種退休規劃方式？",
                                   "options": [
                                     {"label": "穩定領息，不想承擔風險", "value": "conservative"},
                                     {"label": "適度成長，可接受小幅波動", "value": "moderate"},
                                     {"label": "積極投資，追求較高報酬", "value": "aggressive"}
                                   ]
                                 }
                               }

                               // 產品推薦
                               data: {
                                 "type": "tool-call",
                                 "toolCallId": "call_ghi",
                                 "toolName": "get_product_recommendations",
                                 "args": { "context": "...", "question": "...", "verticals": [...] }
                               }

                               data: {
                                 "type": "tool-result",
                                 "toolCallId": "call_ghi",
                                 "result": {
                                   "grouped_results": { ... },
                                   "total_products": 5,
                                   "intent": "retirement_planning"
                                 }
                               }

                               // Intent Profile 更新
                               data: {
                                 "type": "intent-profile-update",
                                 "intentProfile": { ... }
                               }

                               data: {"type": "finish", "finishReason": "stop"}
                               ```

                               ### 4.2 Quick Questions Endpoint

                               **Endpoint:** `GET /api/v1/quick-questions`

                               **Response:**
                               ```json
                               {
                                 "questions": [
                                   {"id": "q1", "text": "勞退自提 6% 真的划算嗎？", "intent_hint": "retirement_planning"},
                                   {"id": "q2", "text": "55歲開始準備退休金來得及嗎？", "intent_hint": "retirement_timing"},
                                   {"id": "q3", "text": "退休後每月需要多少錢？", "intent_hint": "retirement_budget"}
                                 ]
                               }
                               ```

                               ---

                               ## 5. 前端實作規格

                               ### 5.1 技術棧

                               - **Framework:** Next.js 15 (App Router)
                               - - **Chat UI:** assistant-ui
                                 - - **Styling:** Tailwind CSS + shadcn/ui
                                   - - **State:** React Context + useExternalStoreRuntime
                                    
                                     - ### 5.2 專案結構
                                    
                                     - ```
                                       frontend/
                                       ├── app/
                                       │   ├── layout.tsx
                                       │   ├── page.tsx
                                       │   ├── chat/[sessionId]/page.tsx
                                       │   └── providers/ChatRuntimeProvider.tsx
                                       ├── components/
                                       │   ├── assistant-ui/
                                       │   │   ├── thread.tsx
                                       │   │   └── thread-list.tsx
                                       │   ├── chat/
                                       │   │   ├── QuickQuestionChips.tsx
                                       │   │   ├── ChatWidget.tsx
                                       │   │   └── ChatContainer.tsx
                                       │   ├── tools/
                                       │   │   ├── ClarificationToolUI.tsx
                                       │   │   ├── ProductRecommendationToolUI.tsx
                                       │   │   ├── ProductCard.tsx
                                       │   │   └── ProductGrid.tsx
                                       │   └── ui/
                                       │       └── ...shadcn components
                                       ├── hooks/
                                       │   ├── useIntentProfile.ts
                                       │   └── useQuickQuestions.ts
                                       └── lib/
                                           ├── api/chat.ts
                                           └── types/
                                               ├── chat.ts
                                               ├── intent.ts
                                               └── product.ts
                                       ```

                                       ---

                                       ## 6. UI 元件設計

                                       ### 6.1 Quick Question Chips

                                       初始顯示的問題選項，點擊後開始對話。

                                       ### 6.2 Clarification Tool UI

                                       當 AI 需要用戶選擇時顯示的互動式選項按鈕。

                                       ### 6.3 Product Recommendation Tool UI

                                       產品推薦卡片，支援多種 vertical (書籍、旅遊、保險等)。

                                       ---

                                       ## 7. 實作流程

                                       ### Phase 1: 後端 - Chat Agent (Week 1-2)

                                       | 任務 | 說明 |
                                       |------|------|
                                       | 建立 intent_chat agent 結構 | 不修改現有 product_recommendation |
                                       | 實作 ChatState 和 IntentProfile | Pydantic models |
                                       | 封裝 product_recommendation 為 tool | 透過 invoke() 調用 |
                                       | 實作 ask_clarification tool | 返回選項給前端 |
                                       | 實作 SSE streaming endpoint | FastAPI + SSE |

                                       ### Phase 2: 前端 - assistant-ui 整合 (Week 2-3)

                                       | 任務 | 說明 |
                                       |------|------|
                                       | 專案初始化 | Next.js + assistant-ui |
                                       | ChatRuntimeProvider | useExternalStoreRuntime |
                                       | QuickQuestionChips | 初始問題選項 |
                                       | ClarificationToolUI | 選項按鈕 UI |
                                       | ProductRecommendationToolUI | 產品卡片 |

                                       ### Phase 3: 整合測試 (Week 3-4)

                                       | 任務 | 說明 |
                                       |------|------|
                                       | E2E 流程測試 | Discovery → Conversion 完整流程 |
                                       | Intent 累積測試 | 驗證 intent_score 計算 |
                                       | UI/UX 優化 | 響應式、Loading 狀態 |
                                       | 部署準備 | 環境變數、CI/CD |

                                       ---

                                       ## 附錄

                                       ### A. User Journey 完整流程

                                       ```
                                       ┌─────────────────────────────────────────────────────────────────────┐
                                       │                                                                     │
                                       │   [Google Search]                                                   │
                                       │        │                                                            │
                                       │        ▼                                                            │
                                       │   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐        │
                                       │   │Discovery│───▶│Engagement│───▶│Qualify  │───▶│ Bidding │        │
                                       │   │ 遠見文章 │    │AIGC Widget│   │意圖確認  │    │ 競價配對 │        │
                                       │   └─────────┘    └─────────┘    └─────────┘    └─────────┘        │
                                       │        │              │              │              │              │
                                       │   Mlytics      Mlytics        Mlytics        Mlytics            │
                                       │   不介入       開始介入        深度介入        變現點             │
                                       │                                                                     │
                                       │        │              │              │              │              │
                                       │        ▼              ▼              ▼              ▼              │
                                       │   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐        │
                                       │   │Conversion│───▶│Transaction│───▶│Attribution│───▶│ Revenue │    │
                                       │   │ 轉換橋接 │    │  成交    │    │   歸因   │    │  收入   │        │
                                       │   └─────────┘    └─────────┘    └─────────┘    └─────────┘        │
                                       │                                                                     │
                                       └─────────────────────────────────────────────────────────────────────┘
                                       ```

                                       ### B. Intent Profile 範例

                                       ```json
                                       {
                                         "user_id": "anon_12345",
                                         "session": "gvm_article_78901",
                                         "signals": {
                                           "life_stage": "pre-retirement",
                                           "age_estimate": "55-60",
                                           "asset_range": "3M-5M TWD",
                                           "risk_preference": "conservative",
                                           "product_fit": ["annuity", "savings_insurance"],
                                           "intent_score": 78,
                                           "purchase_timeline": "3-6 months"
                                         }
                                       }
                                       ```

                                       ---

                                       **文件版本:** v2.0
                                       **最後更新:** 2026/01/21
                                       **維護者:** Product Engineering Team
