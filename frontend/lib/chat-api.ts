/**
 * Chat API client for communicating with the Intent Chat backend.
 * Handles both SSE streaming and synchronous chat endpoints.
 */

import type {
  Message,
  IntentProfile,
  QuickQuestion,
  StreamCallbacks,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

/**
 * Stream a chat message from the backend using SSE.
 */
export async function streamMessage(
  message: string,
  sessionId: string,
  conversationHistory: Message[],
  callbacks: StreamCallbacks,
  intentProfile?: IntentProfile | null
): Promise<void> {
  const history = conversationHistory.map((m) => ({
    role: m.role,
    content: m.content,
  }));

  try {
    const response = await fetch(`${API_BASE}/api/v1/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(API_KEY && { Authorization: `Bearer ${API_KEY}` }),
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        conversation_history: history,
        intent_profile: intentProfile || undefined,
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          // Event type line - we'll parse data on next line
          continue;
        }

        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));

            if (data.response) {
              callbacks.onTextDelta(data.response);
            }

            if (data.intent_profile) {
              callbacks.onIntentProfile?.(data.intent_profile);
            }

            if (data.tool_calls && data.tool_calls.length > 0) {
              for (const tc of data.tool_calls) {
                callbacks.onToolCall?.(tc);
              }
            }

            if (data.error) {
              callbacks.onError?.(new Error(data.error));
            }
          } catch {
            // Skip malformed JSON lines
          }
        }
      }
    }

    callbacks.onFinish?.();
  } catch (error) {
    callbacks.onError?.(error instanceof Error ? error : new Error(String(error)));
  }
}

/**
 * Send a synchronous chat message (non-streaming).
 */
export async function sendMessageSync(
  message: string,
  sessionId: string,
  conversationHistory: Message[]
): Promise<{ response: string; intentProfile: IntentProfile }> {
  const history = conversationHistory.map((m) => ({
    role: m.role,
    content: m.content,
  }));

  const response = await fetch(`${API_BASE}/api/v1/chat/sync`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY && { Authorization: `Bearer ${API_KEY}` }),
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      conversation_history: history,
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat API error: ${response.status}`);
  }

  const data = await response.json();
  return {
    response: data.response,
    intentProfile: data.intent_profile,
  };
}

/**
 * Fetch quick questions from the backend.
 */
export async function fetchQuickQuestions(): Promise<QuickQuestion[]> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/quick-questions`, {
      headers: {
        ...(API_KEY && { Authorization: `Bearer ${API_KEY}` }),
      },
    });

    if (!response.ok) {
      throw new Error(`Quick questions API error: ${response.status}`);
    }

    const data = await response.json();
    return data.questions;
  } catch (error) {
    console.error("Failed to fetch quick questions:", error);
    return [];
  }
}
