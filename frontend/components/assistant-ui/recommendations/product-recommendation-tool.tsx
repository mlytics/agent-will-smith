"use client";

import { memo } from "react";
import { CheckIcon, LoaderIcon, AlertCircleIcon } from "lucide-react";
import type { ToolCallMessagePartComponent } from "@assistant-ui/react";
import type { ProductRecommendationResult } from "@/lib/types";
import { ProductRecommendations } from "./product-recommendations";
import { cn } from "@/lib/utils";

/**
 * Custom tool UI for product_recommendation tool results.
 * Renders beautiful cards instead of raw JSON.
 */
const ProductRecommendationToolImpl: ToolCallMessagePartComponent = ({
  toolName,
  result,
  status,
}) => {
  const isRunning = status?.type === "running";
  const isComplete = status?.type === "complete";
  const hasError = status?.type === "incomplete";

  // Parse the result as ProductRecommendationResult
  const recommendationResult = result as ProductRecommendationResult | undefined;

  // Loading state
  if (isRunning) {
    return (
      <div className="my-4 flex items-center gap-3 rounded-2xl border border-amber-200/60 bg-amber-50/50 p-4 dark:border-amber-800/40 dark:bg-amber-950/20">
        <LoaderIcon className="h-5 w-5 animate-spin text-amber-600 dark:text-amber-400" />
        <span className="text-sm font-medium text-amber-700 dark:text-amber-300">
          正在搜尋相關推薦內容...
        </span>
      </div>
    );
  }

  // Error state
  if (hasError) {
    const errorMessage =
      status.error && typeof status.error === "string"
        ? status.error
        : "無法載入推薦內容";

    return (
      <div className="my-4 flex items-center gap-3 rounded-2xl border border-red-200/60 bg-red-50/50 p-4 dark:border-red-800/40 dark:bg-red-950/20">
        <AlertCircleIcon className="h-5 w-5 text-red-500 dark:text-red-400" />
        <span className="text-sm text-red-700 dark:text-red-300">
          {errorMessage}
        </span>
      </div>
    );
  }

  // No result yet
  if (!recommendationResult) {
    return null;
  }

  // Success - render the recommendations
  return (
    <div className="my-4">
      <ProductRecommendations result={recommendationResult} />
    </div>
  );
};

export const ProductRecommendationTool = memo(
  ProductRecommendationToolImpl
) as ToolCallMessagePartComponent;

ProductRecommendationTool.displayName = "ProductRecommendationTool";
