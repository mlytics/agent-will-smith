"use client";

import { CalendarIcon, MapPinIcon, UserIcon, ExternalLinkIcon } from "lucide-react";
import type { ProductResult, ActivityMetadata } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ActivityCardProps {
  product: ProductResult;
  className?: string;
}

function formatDateTime(isoString: string | null | undefined): string {
  if (!isoString) return "";
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString("zh-TW", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}

export function ActivityCard({ product, className }: ActivityCardProps) {
  const metadata = product.metadata as ActivityMetadata;
  const coverImage = metadata.cover_image_urls?.[0];
  const hasTime = metadata.start_time || metadata.end_time;

  return (
    <a
      href={metadata.permalink_url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-2xl border border-border/60",
        "bg-gradient-to-br from-card via-card to-emerald-50/30 dark:to-emerald-950/20",
        "shadow-sm transition-all duration-300",
        "hover:border-emerald-300 hover:shadow-lg hover:shadow-emerald-100/50",
        "dark:hover:border-emerald-800 dark:hover:shadow-emerald-900/20",
        className
      )}
    >
      {/* Cover Image */}
      {coverImage && (
        <div className="relative h-32 w-full overflow-hidden bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900/30 dark:to-teal-900/30">
          <img
            src={coverImage}
            alt={product.title}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
          {/* Category Badge */}
          {metadata.category && (
            <span className="absolute bottom-2 left-2 rounded-full bg-emerald-600/90 px-2.5 py-0.5 text-xs font-medium text-white backdrop-blur-sm">
              {metadata.category}
            </span>
          )}
        </div>
      )}

      {/* Content */}
      <div className="flex flex-1 flex-col p-4">
        {/* Title */}
        <h4 className="mb-2 line-clamp-2 text-sm font-semibold leading-snug text-foreground group-hover:text-emerald-700 dark:group-hover:text-emerald-400">
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
          {/* Time */}
          {hasTime && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <CalendarIcon className="h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
              <span className="truncate">
                {formatDateTime(metadata.start_time)}
                {metadata.end_time && ` - ${formatDateTime(metadata.end_time)}`}
              </span>
            </div>
          )}

          {/* Location */}
          {(metadata.location_name || metadata.location_address) && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <MapPinIcon className="h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
              <span className="truncate">
                {metadata.location_name || metadata.location_address}
              </span>
            </div>
          )}

          {/* Organizer */}
          {metadata.organizer && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <UserIcon className="h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
              <span className="truncate">{metadata.organizer}</span>
            </div>
          )}
        </div>

        {/* Link indicator */}
        <div className="mt-3 flex items-center justify-end text-xs font-medium text-emerald-600 opacity-0 transition-opacity group-hover:opacity-100 dark:text-emerald-400">
          <span>查看詳情</span>
          <ExternalLinkIcon className="ml-1 h-3 w-3" />
        </div>
      </div>
    </a>
  );
}
