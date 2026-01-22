"use client";

/**
 * SessionStats - Simple display showing conversation turns and signals count.
 */

import { MessageSquareIcon, ZapIcon } from "lucide-react";

interface SessionStatsProps {
  turnCount: number;
  signalCount: number;
}

export function SessionStats({ turnCount, signalCount }: SessionStatsProps) {
  return (
    <div className="flex items-center justify-center gap-6 py-3 px-4 text-xs text-muted-foreground border-t border-border/50">
      <div className="flex items-center gap-1.5">
        <MessageSquareIcon className="h-3.5 w-3.5" />
        <span>Turns: {turnCount}</span>
      </div>
      <div className="w-px h-4 bg-border" />
      <div className="flex items-center gap-1.5">
        <ZapIcon className="h-3.5 w-3.5" />
        <span>Signals: {signalCount}</span>
      </div>
    </div>
  );
}
