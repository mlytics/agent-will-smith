"use client";

/**
 * Main chat page with sidebar layout.
 * Displays the chat thread and intent profile panel.
 */

import { Thread } from "@/components/assistant-ui/thread";
import { IntentProfilePanel } from "@/components/assistant-ui/intent-profile-panel";
import { RuntimeProvider } from "@/lib/runtime-provider";
import { useState } from "react";
import { PanelRightCloseIcon, PanelRightOpenIcon, SparklesIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ChatPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <RuntimeProvider>
      <div className="flex h-full flex-col">
        {/* Header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/50 bg-card/80 px-4 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 shadow-sm">
              <SparklesIcon className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-tight">
                Intent Advisor
              </h1>
              <p className="text-xs text-muted-foreground">
                Smart Financial Guidance
              </p>
            </div>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-muted-foreground hover:text-foreground"
            aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            {sidebarOpen ? (
              <PanelRightCloseIcon className="h-5 w-5" />
            ) : (
              <PanelRightOpenIcon className="h-5 w-5" />
            )}
          </Button>
        </header>

        {/* Main content */}
        <div className="flex flex-1 overflow-hidden">
          {/* Chat area */}
          <main className="flex-1 overflow-hidden">
            <Thread />
          </main>

          {/* Intent profile sidebar */}
          <aside
            className={`
              shrink-0 overflow-hidden border-l border-border/50 bg-sidebar transition-all duration-300 ease-in-out
              ${sidebarOpen ? "w-80" : "w-0"}
            `}
          >
            <div className="h-full w-80 overflow-y-auto p-5 scrollbar-refined">
              <IntentProfilePanel />
            </div>
          </aside>
        </div>
      </div>
    </RuntimeProvider>
  );
}
