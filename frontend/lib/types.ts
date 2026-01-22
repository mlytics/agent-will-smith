/**
 * Type definitions for the Intent Chat frontend.
 */

// Content parts for assistant-ui messages
export interface TextContentPart {
  type: "text";
  text: string;
}

export interface ToolCallContentPart {
  type: "tool-call";
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
  result?: unknown;
}

export type ContentPart = TextContentPart | ToolCallContentPart;

export interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string | ContentPart[];
  createdAt?: Date;
}

// =============================================================================
// Intent Signal Types
// =============================================================================

export interface IntentSignal {
  signal_type: "explicit" | "inferred" | "clarified";
  category: string;
  confidence: number;
  timestamp: string;
}

export interface FinancialGoal {
  target_age?: number | null;
  target_amount?: string | null;
  timeline?: string | null;
  goal_type?: string | null;
}

export interface IntentProfile {
  life_stage: string | null;
  risk_preference: "conservative" | "moderate" | "aggressive" | null;
  product_interests: string[];
  intent_score: number;
  signals: IntentSignal[];
  financial_goal: FinancialGoal | null;
  current_assets: string | null;
  investment_experience: "beginner" | "intermediate" | "experienced" | null;
}

export interface QuickQuestion {
  id: string;
  text: string;
  category: string;
}

export interface ChatRequest {
  message: string;
  session_id: string;
  context?: Record<string, unknown>;
  conversation_history?: { role: string; content: string }[];
}

export interface ChatResponse {
  response: string;
  intent_profile: IntentProfile;
  tool_calls: Array<{
    tool_call_id: string;
    result: Record<string, unknown>;
    error?: string;
  }>;
  session_id: string;
  is_complete: boolean;
}

export interface QuickQuestionsResponse {
  questions: QuickQuestion[];
}

export interface StreamCallbacks {
  onTextDelta: (text: string) => void;
  onIntentProfile?: (profile: IntentProfile) => void;
  onToolCall?: (toolCall: {
    tool_call_id: string;
    name: string;
    args?: Record<string, unknown>;
    result: Record<string, unknown>;
  }) => void;
  onFinish?: () => void;
  onError?: (error: Error) => void;
}

// =============================================================================
// Product Recommendation Types
// =============================================================================

export type ProductVertical = "activities" | "books" | "articles";

export interface ActivityMetadata {
  category?: string | null;
  organizer?: string | null;
  location_name?: string | null;
  location_address?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  permalink_url?: string | null;
  cover_image_urls?: string[];
}

export interface BookMetadata {
  title_subtitle?: string | null;
  authors?: string[];
  categories?: string[];
  permalink_url?: string | null;
  cover_image_url?: string | null;
  prices?: string[];
}

export interface ArticleMetadata {
  authors?: string[];
  keywords?: string[];
  categories?: string[];
  permalink_url?: string | null;
  thumbnail_url?: string | null;
  main_image_url?: string | null;
  publish_time?: string | null;
}

export type ProductMetadata = ActivityMetadata | BookMetadata | ArticleMetadata;

export interface ProductResult {
  product_id: string;
  vertical: ProductVertical;
  title: string;
  description?: string | null;
  relevance_score: number;
  metadata: ProductMetadata;
}

export interface ProductRecommendationResult {
  grouped_results: {
    activities?: ProductResult[];
    books?: ProductResult[];
    articles?: ProductResult[];
  };
  total_products: number;
  status: "complete" | "partial";
  errors?: Record<string, string>;
  intent?: string;
}
