"use client";

/**
 * Runtime provider that connects assistant-ui to our custom SSE backend.
 * Uses useExternalStoreRuntime for full control over message state.
 */

import { useState, useCallback, type ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  useExternalStoreRuntime,
  type AppendMessage,
} from "@assistant-ui/react";
import { streamMessage, sendMessageSync } from "./chat-api";
import { useIntentProfile, IntentProfileProvider } from "./intent-profile-context";
import type { Message, IntentProfile } from "./types";

// Convert our Message type to ThreadMessageLike format
function convertMessage(msg: Message, idx: number) {
  return {
    id: msg.id || `msg-${idx}`,
    role: msg.role as "user" | "assistant",
    content: msg.content || "",
    createdAt: msg.createdAt || new Date(),
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
  const { profile, updateProfile } = useIntentProfile();

  const onNew = useCallback(
    async (message: AppendMessage) => {
      const userMessage = fromAppendMessage(message);

      // Add user message immediately
      setMessages((prev) => [...prev, userMessage]);
      setIsRunning(true);

      // Create placeholder for assistant message
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: "",
        createdAt: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      try {
        // Use streaming endpoint, pass current intent profile for state persistence
        await streamMessage(
          userMessage.content,
          sessionId,
          messages,
          {
            onTextDelta: (text) => {
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastIdx = newMessages.length - 1;
                if (newMessages[lastIdx]?.role === "assistant") {
                  newMessages[lastIdx] = {
                    ...newMessages[lastIdx],
                    content: text,
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
          profile  // Pass current intent profile for state persistence
        );
      } catch (error) {
        console.error("Chat error:", error);
        // Fallback to sync endpoint
        try {
          const { response, intentProfile } = await sendMessageSync(
            userMessage.content,
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
    [messages, sessionId, updateProfile, profile]
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
    <IntentProfileProvider>
      <RuntimeProviderInner>{children}</RuntimeProviderInner>
    </IntentProfileProvider>
  );
}
