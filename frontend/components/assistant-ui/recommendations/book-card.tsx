"use client";

import { BookOpenIcon, UserIcon, TagIcon, ExternalLinkIcon } from "lucide-react";
import type { ProductResult, BookMetadata } from "@/lib/types";
import { cn } from "@/lib/utils";

interface BookCardProps {
  product: ProductResult;
  className?: string;
}

export function BookCard({ product, className }: BookCardProps) {
  const metadata = product.metadata as BookMetadata;
  const authors = metadata.authors?.slice(0, 2) || [];
  const categories = metadata.categories?.slice(0, 2) || [];
  const price = metadata.prices?.[0];

  return (
    <a
      href={metadata.permalink_url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "group relative flex gap-3 overflow-hidden rounded-2xl border border-border/60 p-3",
        "bg-gradient-to-br from-card via-card to-amber-50/30 dark:to-amber-950/20",
        "shadow-sm transition-all duration-300",
        "hover:border-amber-300 hover:shadow-lg hover:shadow-amber-100/50",
        "dark:hover:border-amber-800 dark:hover:shadow-amber-900/20",
        className
      )}
    >
      {/* Book Cover */}
      <div className="relative h-28 w-20 shrink-0 overflow-hidden rounded-lg bg-gradient-to-br from-amber-100 to-orange-100 shadow-md dark:from-amber-900/30 dark:to-orange-900/30">
        {metadata.cover_image_url ? (
          <img
            src={metadata.cover_image_url}
            alt={product.title}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <BookOpenIcon className="h-8 w-8 text-amber-400/60 dark:text-amber-600/60" />
          </div>
        )}
        {/* Price Badge */}
        {price && (
          <span className="absolute bottom-1 right-1 rounded bg-amber-600/90 px-1.5 py-0.5 text-[10px] font-semibold text-white">
            {price}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col overflow-hidden py-0.5">
        {/* Title */}
        <h4 className="mb-1 line-clamp-2 text-sm font-semibold leading-snug text-foreground group-hover:text-amber-700 dark:group-hover:text-amber-400">
          {product.title}
        </h4>

        {/* Subtitle */}
        {metadata.title_subtitle && (
          <p className="mb-1.5 line-clamp-1 text-xs text-muted-foreground">
            {metadata.title_subtitle}
          </p>
        )}

        {/* Authors */}
        {authors.length > 0 && (
          <div className="mb-2 flex items-center gap-1.5 text-xs text-muted-foreground">
            <UserIcon className="h-3 w-3 shrink-0 text-amber-600 dark:text-amber-400" />
            <span className="truncate">
              {authors.join(", ")}
              {(metadata.authors?.length || 0) > 2 && " 等"}
            </span>
          </div>
        )}

        {/* Categories */}
        {categories.length > 0 && (
          <div className="mt-auto flex flex-wrap gap-1">
            {categories.map((cat, i) => (
              <span
                key={i}
                className="inline-flex items-center rounded-full bg-amber-100/80 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
              >
                {cat}
              </span>
            ))}
          </div>
        )}

        {/* Link indicator */}
        <div className="mt-2 flex items-center justify-end text-xs font-medium text-amber-600 opacity-0 transition-opacity group-hover:opacity-100 dark:text-amber-400">
          <span>立即閱讀</span>
          <ExternalLinkIcon className="ml-1 h-3 w-3" />
        </div>
      </div>
    </a>
  );
}
