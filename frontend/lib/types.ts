/**
 * Type definitions for the Intent Chat frontend.
 */

export interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  createdAt?: Date;
}

export interface IntentProfile {
  life_stage: string | null;
  risk_preference: "conservative" | "moderate" | "aggressive" | null;
  product_interests: string[];
  intent_score: number;
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
  onToolCall?: (toolCall: { tool_call_id: string; result: Record<string, unknown> }) => void;
  onFinish?: () => void;
  onError?: (error: Error) => void;
}
