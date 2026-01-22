"use client";

/**
 * SignalHistory - Collapsible list showing intent signals captured during conversation.
 * Shows most recent 10 signals.
 */

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { ChevronDownIcon, ScrollTextIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { IntentSignal } from "@/lib/types";

interface SignalHistoryProps {
  signals: IntentSignal[];
}

const signalTypeColors = {
  explicit: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  inferred: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  clarified: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
};

function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return "";
  }
}

function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

export function SignalHistory({ signals }: SignalHistoryProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (signals.length === 0) {
    return null;
  }

  // Show most recent 10 signals
  const displaySignals = signals.slice(-10).reverse();

  return (
    <Card className="border-0 bg-card shadow-sm">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <CardContent className="pt-4 pb-4 cursor-pointer hover:bg-secondary/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ScrollTextIcon className="h-4 w-4 text-muted-foreground" />
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Signal History
                </p>
                <Badge variant="secondary" className="text-xs">
                  {signals.length}
                </Badge>
              </div>
              <ChevronDownIcon
                className={cn(
                  "h-4 w-4 text-muted-foreground transition-transform",
                  isOpen && "rotate-180"
                )}
              />
            </div>
          </CardContent>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4">
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {displaySignals.map((signal, index) => (
                <div
                  key={index}
                  className="flex items-start justify-between py-2 border-b border-border/50 last:border-0"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground font-mono">
                        {formatTimestamp(signal.timestamp)}
                      </span>
                      <span className="text-sm font-medium capitalize">
                        {signal.category.replace(/_/g, " ")}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="secondary"
                        className={cn(
                          "text-xs border-0",
                          signalTypeColors[signal.signal_type]
                        )}
                      >
                        {signal.signal_type}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatConfidence(signal.confidence)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
