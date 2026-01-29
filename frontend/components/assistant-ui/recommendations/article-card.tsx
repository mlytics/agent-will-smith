"use client";

import { FileTextIcon, UserIcon, ClockIcon, TagIcon, ExternalLinkIcon } from "lucide-react";
import type { ProductResult, ArticleMetadata } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ArticleCardProps {
  product: ProductResult;
  className?: string;
}

function formatPublishDate(isoString: string | null | undefined): string {
  if (!isoString) return "";
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "今天";
    if (diffDays === 1) return "昨天";
    if (diffDays < 7) return `${diffDays} 天前`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} 週前`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} 個月前`;

    return date.toLocaleDateString("zh-TW", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return isoString;
  }
}

export function ArticleCard({ product, className }: ArticleCardProps) {
  const metadata = product.metadata as ArticleMetadata;
  const authors = metadata.authors?.slice(0, 2) || [];
  const keywords = metadata.keywords?.slice(0, 3) || [];
  const imageUrl = metadata.main_image_url || metadata.thumbnail_url;

  return (
    <a
      href={metadata.permalink_url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-2xl border border-border/60",
        "bg-gradient-to-br from-card via-card to-blue-50/30 dark:to-blue-950/20",
        "shadow-sm transition-all duration-300",
        "hover:border-blue-300 hover:shadow-lg hover:shadow-blue-100/50",
        "dark:hover:border-blue-800 dark:hover:shadow-blue-900/20",
        className
      )}
    >
      {/* Thumbnail */}
      {imageUrl && (
        <div className="relative h-28 w-full overflow-hidden bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/30">
          <img
            src={imageUrl}
            alt={product.title}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
        </div>
      )}

      {/* Content */}
      <div className="flex flex-1 flex-col p-4">
        {/* Title */}
        <h4 className="mb-2 line-clamp-2 text-sm font-semibold leading-snug text-foreground group-hover:text-blue-700 dark:group-hover:text-blue-400">
          {product.title}
        </h4>

        {/* Description */}
        {product.description && (
          <p className="mb-3 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
            {product.description}
          </p>
        )}

        {/* Metadata */}
        <div className="mt-auto space-y-1.5">
          {/* Author & Date */}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            {authors.length > 0 && (
              <div className="flex items-center gap-1">
                <UserIcon className="h-3 w-3 shrink-0 text-blue-600 dark:text-blue-400" />
                <span className="truncate">
                  {authors.join(", ")}
                </span>
              </div>
            )}
            {metadata.publish_time && (
              <div className="flex items-center gap-1">
                <ClockIcon className="h-3 w-3 shrink-0 text-blue-600 dark:text-blue-400" />
                <span>{formatPublishDate(metadata.publish_time)}</span>
              </div>
            )}
          </div>

          {/* Keywords/Tags */}
          {keywords.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {keywords.map((keyword, i) => (
                <span
                  key={i}
                  className="inline-flex items-center rounded-full bg-blue-100/80 px-2 py-0.5 text-[10px] font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                >
                  #{keyword}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Link indicator */}
        <div className="mt-3 flex items-center justify-end text-xs font-medium text-blue-600 opacity-0 transition-opacity group-hover:opacity-100 dark:text-blue-400">
          <span>閱讀全文</span>
          <ExternalLinkIcon className="ml-1 h-3 w-3" />
        </div>
      </div>
    </a>
  );
}
