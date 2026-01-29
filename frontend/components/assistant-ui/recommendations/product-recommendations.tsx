"use client";

import { BookOpenIcon, CalendarIcon, FileTextIcon, SparklesIcon } from "lucide-react";
import type { ProductRecommendationResult, ProductResult } from "@/lib/types";
import { ActivityCard } from "./activity-card";
import { BookCard } from "./book-card";
import { ArticleCard } from "./article-card";
import { cn } from "@/lib/utils";

interface ProductRecommendationsProps {
  result: ProductRecommendationResult;
  className?: string;
}

interface SectionConfig {
  key: "activities" | "books" | "articles";
  title: string;
  icon: typeof CalendarIcon;
  color: string;
  CardComponent: React.ComponentType<{ product: ProductResult; className?: string }>;
}

const sections: SectionConfig[] = [
  {
    key: "activities",
    title: "相關活動",
    icon: CalendarIcon,
    color: "text-emerald-600 dark:text-emerald-400",
    CardComponent: ActivityCard,
  },
  {
    key: "books",
    title: "推薦書籍",
    icon: BookOpenIcon,
    color: "text-amber-600 dark:text-amber-400",
    CardComponent: BookCard,
  },
  {
    key: "articles",
    title: "相關文章",
    icon: FileTextIcon,
    color: "text-blue-600 dark:text-blue-400",
    CardComponent: ArticleCard,
  },
];

export function ProductRecommendations({ result, className }: ProductRecommendationsProps) {
  const { grouped_results, total_products, intent } = result;

  if (total_products === 0) {
    return (
      <div className={cn("rounded-2xl border border-dashed border-border/60 p-6 text-center", className)}>
        <SparklesIcon className="mx-auto mb-3 h-8 w-8 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">
          目前沒有找到相關的推薦內容
        </p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header with intent */}
      {intent && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <SparklesIcon className="h-4 w-4 text-amber-500" />
          <span>
            根據您的需求「<span className="font-medium text-foreground">{intent}</span>」，為您推薦：
          </span>
        </div>
      )}

      {/* Sections */}
      {sections.map(({ key, title, icon: Icon, color, CardComponent }) => {
        const products = grouped_results[key];
        if (!products || products.length === 0) return null;

        return (
          <div key={key} className="space-y-3">
            {/* Section Header */}
            <div className="flex items-center gap-2">
              <Icon className={cn("h-4 w-4", color)} />
              <h3 className="text-sm font-semibold text-foreground">
                {title}
              </h3>
              <span className="text-xs text-muted-foreground">
                ({products.length})
              </span>
            </div>

            {/* Cards Grid */}
            <div className="grid gap-3 sm:grid-cols-2">
              {products.slice(0, 4).map((product) => (
                <CardComponent
                  key={product.product_id}
                  product={product}
                />
              ))}
            </div>
          </div>
        );
      })}

      {/* Status indicator for partial results */}
      {result.status === "partial" && (
        <div className="text-center text-xs text-muted-foreground">
          部分結果可能因載入問題而未顯示
        </div>
      )}
    </div>
  );
}
