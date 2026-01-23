"use client";

/**
 * Runtime provider that connects assistant-ui to our custom SSE backend.
 * Uses useExternalStoreRuntime for full control over message state.
 */

import { useState, useCallback, useRef, type ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  useExternalStoreRuntime,
  type AppendMessage,
  type ThreadMessageLike,
} from "@assistant-ui/react";
import { streamMessage, sendMessageSync } from "./chat-api";
import { useIntentProfile, IntentProfileProvider } from "./intent-profile-context";
import { ScenarioProvider, useScenario } from "./scenario-context";
import type { Message, IntentProfile, ContentPart, ToolCallContentPart } from "./types";

// Convert our Message type to ThreadMessageLike format for assistant-ui
function convertMessage(msg: Message, idx: number): ThreadMessageLike {
  const id = msg.id || `msg-${idx}`;
  const createdAt = msg.createdAt || new Date();

  // User messages are always simple text
  if (msg.role === "user") {
    const textContent = typeof msg.content === "string"
      ? msg.content
      : msg.content.find(p => p.type === "text")?.text || "";
    return {
      id,
      role: "user",
      content: [{ type: "text", text: textContent }],
      createdAt,
    };
  }

  // Assistant messages may have text and tool-call parts
  if (typeof msg.content === "string") {
    return {
      id,
      role: "assistant",
      content: [{ type: "text", text: msg.content }],
      createdAt,
    };
  }

  // Content is already an array of parts - build and cast to expected type
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const parts: any[] = [];
  for (const part of msg.content) {
    if (part.type === "text") {
      parts.push({ type: "text", text: part.text });
    } else if (part.type === "tool-call") {
      parts.push({
        type: "tool-call",
        toolCallId: part.toolCallId,
        toolName: part.toolName,
        args: part.args,
        result: part.result,
      });
    }
  }

  return {
    id,
    role: "assistant",
    content: parts,
    createdAt,
  };
}

// Convert assistant-ui AppendMessage to our Message type
function fromAppendMessage(msg: AppendMessage): Message {
  // Extract text from content
  let text = "";

  if (msg.content) {
    if (typeof msg.content === "string") {
      text = msg.content;
    } else if (Array.isArray(msg.content)) {
      for (const part of msg.content) {
        if (part && typeof part === "object" && "type" in part && part.type === "text" && "text" in part) {
          text = (part as { type: "text"; text: string }).text;
          break;
        }
      }
    }
  }

  return {
    id: `user-${Date.now()}`,
    role: "user",
    content: text,
    createdAt: new Date(),
  };
}

function RuntimeProviderInner({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const { profile, updateProfile, incrementTurnCount } = useIntentProfile();
  const { selectedScenario } = useScenario();

  // Use ref to accumulate tool calls during streaming
  const pendingToolCallsRef = useRef<ToolCallContentPart[]>([]);

  const onNew = useCallback(
    async (message: AppendMessage) => {
      // Track conversation turns for analytics
      incrementTurnCount();

      const userMessage = fromAppendMessage(message);

      // Add user message immediately
      setMessages((prev) => [...prev, userMessage]);
      setIsRunning(true);

      // Reset pending tool calls
      pendingToolCallsRef.current = [];

      // Create placeholder for assistant message
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: "",
        createdAt: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Extract text content from user message (always a string for user messages)
      const messageText = typeof userMessage.content === "string"
        ? userMessage.content
        : userMessage.content.find(p => p.type === "text")?.text || "";

      try {
        // Use streaming endpoint, pass current intent profile for state persistence
        await streamMessage(
          messageText,
          sessionId,
          messages,
          {
            onTextDelta: (text) => {
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastIdx = newMessages.length - 1;
                if (newMessages[lastIdx]?.role === "assistant") {
                  // Build content parts with text and any pending tool calls
                  const contentParts: ContentPart[] = [
                    { type: "text", text },
                  ];
                  // Add tool calls if any
                  for (const tc of pendingToolCallsRef.current) {
                    contentParts.push(tc);
                  }

                  newMessages[lastIdx] = {
                    ...newMessages[lastIdx],
                    content: contentParts,
                  };
                }
                return newMessages;
              });
            },
            onToolCall: (toolCall) => {
              // Accumulate tool calls
              const toolCallPart: ToolCallContentPart = {
                type: "tool-call",
                toolCallId: toolCall.tool_call_id,
                toolName: toolCall.name || "product_recommendation",
                args: toolCall.args || {},
                result: toolCall.result,
              };
              pendingToolCallsRef.current.push(toolCallPart);

              // Update message with tool call
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastIdx = newMessages.length - 1;
                if (newMessages[lastIdx]?.role === "assistant") {
                  const currentContent = newMessages[lastIdx].content;
                  let textContent = "";
                  const existingToolCalls: ToolCallContentPart[] = [];

                  if (typeof currentContent === "string") {
                    textContent = currentContent;
                  } else if (Array.isArray(currentContent)) {
                    for (const part of currentContent) {
                      if (part.type === "text") {
                        textContent = part.text;
                      } else if (part.type === "tool-call") {
                        existingToolCalls.push(part);
                      }
                    }
                  }

                  const contentParts: ContentPart[] = [
                    { type: "text", text: textContent },
                    ...existingToolCalls,
                    toolCallPart,
                  ];

                  newMessages[lastIdx] = {
                    ...newMessages[lastIdx],
                    content: contentParts,
                  };
                }
                return newMessages;
              });
            },
            onIntentProfile: (newProfile: IntentProfile) => {
              updateProfile(newProfile);
            },
            onFinish: () => {
              setIsRunning(false);
            },
            onError: (error) => {
              console.error("Stream error:", error);
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastIdx = newMessages.length - 1;
                if (newMessages[lastIdx]?.role === "assistant") {
                  newMessages[lastIdx] = {
                    ...newMessages[lastIdx],
                    content: "Sorry, I encountered an error. Please try again.",
                  };
                }
                return newMessages;
              });
              setIsRunning(false);
            },
          },
          profile,  // Pass current intent profile for state persistence
          { scenario_id: selectedScenario.id }  // Pass scenario context for analytics
        );
      } catch (error) {
        console.error("Chat error:", error);
        // Fallback to sync endpoint
        try {
          const { response, intentProfile } = await sendMessageSync(
            messageText,
            sessionId,
            messages
          );
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            if (newMessages[lastIdx]?.role === "assistant") {
              newMessages[lastIdx] = {
                ...newMessages[lastIdx],
                content: response,
              };
            }
            return newMessages;
          });
          updateProfile(intentProfile);
        } catch (syncError) {
          console.error("Sync fallback error:", syncError);
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            if (newMessages[lastIdx]?.role === "assistant") {
              newMessages[lastIdx] = {
                ...newMessages[lastIdx],
                content: "Sorry, I encountered an error connecting to the server.",
              };
            }
            return newMessages;
          });
        }
        setIsRunning(false);
      }
    },
    [messages, sessionId, updateProfile, profile, incrementTurnCount, selectedScenario]
  );

  // Create adapter with convertMessage for custom message format
  const runtime = useExternalStoreRuntime({
    isRunning,
    messages,
    convertMessage,
    onNew,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}

export function RuntimeProvider({ children }: { children: ReactNode }) {
  return (
    <ScenarioProvider>
      <IntentProfileProvider>
        <RuntimeProviderInner>{children}</RuntimeProviderInner>
      </IntentProfileProvider>
    </ScenarioProvider>
  );
}
