"use client";

/**
 * Hook to fetch and manage quick questions from the backend.
 */

import { useState, useEffect } from "react";
import { fetchQuickQuestions } from "@/lib/chat-api";
import type { QuickQuestion } from "@/lib/types";

export function useQuickQuestions() {
  const [questions, setQuestions] = useState<QuickQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadQuestions() {
      setIsLoading(true);
      setError(null);

      try {
        const data = await fetchQuickQuestions();
        if (!cancelled) {
          setQuestions(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadQuestions();

    return () => {
      cancelled = true;
    };
  }, []);

  return { questions, isLoading, error };
}
