"use client";

/**
 * Custom Thread component with refined financial advisor styling.
 * Integrates dynamic quick questions from the backend API.
 */

import {
  ComposerAddAttachment,
  ComposerAttachments,
  UserMessageAttachments,
} from "@/components/assistant-ui/attachment";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { ToolFallback } from "@/components/assistant-ui/tool-fallback";
import { ProductRecommendationTool } from "@/components/assistant-ui/recommendations";
import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useQuickQuestions } from "@/hooks/use-quick-questions";
import {
  ActionBarMorePrimitive,
  ActionBarPrimitive,
  AssistantIf,
  BranchPickerPrimitive,
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useThreadRuntime,
} from "@assistant-ui/react";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CopyIcon,
  DownloadIcon,
  MoreHorizontalIcon,
  PencilIcon,
  RefreshCwIcon,
  SendHorizonalIcon,
  SparklesIcon,
  SquareIcon,
  TrendingUpIcon,
  WalletIcon,
} from "lucide-react";
import type { FC } from "react";

export const Thread: FC = () => {
  return (
    <ThreadPrimitive.Root
      className="aui-root aui-thread-root @container flex h-full flex-col bg-background bg-pattern"
      style={{
        ["--thread-max-width" as string]: "48rem",
      }}
    >
      <ThreadPrimitive.Viewport
        turnAnchor="top"
        className="aui-thread-viewport scrollbar-refined relative flex flex-1 flex-col overflow-x-auto overflow-y-scroll scroll-smooth px-4 pt-6"
      >
        <AssistantIf condition={({ thread }) => thread.isEmpty}>
          <ThreadWelcome />
        </AssistantIf>

        <ThreadPrimitive.Messages
          components={{
            UserMessage,
            EditComposer,
            AssistantMessage,
          }}
        />

        <ThreadPrimitive.ViewportFooter className="aui-thread-viewport-footer sticky bottom-0 mx-auto mt-auto flex w-full max-w-(--thread-max-width) flex-col gap-4 overflow-visible rounded-t-3xl bg-gradient-to-t from-background via-background to-transparent pb-6 pt-8 md:pb-8">
          <ThreadScrollToBottom />
          <Composer />
        </ThreadPrimitive.ViewportFooter>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
};

const ThreadScrollToBottom: FC = () => {
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip="Scroll to bottom"
        variant="outline"
        className="aui-thread-scroll-to-bottom absolute -top-12 z-10 self-center rounded-full border-border/50 bg-card p-4 shadow-lg disabled:invisible dark:bg-card dark:hover:bg-accent"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  );
};

const ThreadWelcome: FC = () => {
  return (
    <div className="aui-thread-welcome-root mx-auto my-auto flex w-full max-w-(--thread-max-width) grow flex-col">
      <div className="aui-thread-welcome-center flex w-full grow flex-col items-center justify-center">
        <div className="aui-thread-welcome-message flex size-full flex-col items-center justify-center px-4 text-center">
          {/* Logo / Icon */}
          <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 via-amber-500 to-amber-600 shadow-xl shadow-amber-500/20 animate-fade-in-up">
            <SparklesIcon className="h-8 w-8 text-white" />
          </div>

          <h1
            className="aui-thread-welcome-message-inner text-gradient-gold text-3xl font-bold tracking-tight animate-fade-in-up md:text-4xl"
            style={{ animationDelay: "100ms" }}
          >
            Intent Advisor
          </h1>

          <p
            className="aui-thread-welcome-message-inner mt-3 max-w-md text-lg text-muted-foreground animate-fade-in-up"
            style={{ animationDelay: "200ms" }}
          >
            Your intelligent financial companion. Tell me about your goals and
            I'll help guide your investment journey.
          </p>

          {/* Decorative line */}
          <div
            className="decorative-line my-8 w-24 animate-fade-in-up"
            style={{ animationDelay: "300ms" }}
          />
        </div>
      </div>
      <ThreadSuggestions />
    </div>
  );
};

// Category icons for quick questions
const categoryIcons: Record<string, typeof TrendingUpIcon> = {
  investment: TrendingUpIcon,
  retirement: WalletIcon,
  planning: SparklesIcon,
  risk: TrendingUpIcon,
};

const ThreadSuggestions: FC = () => {
  const { questions, isLoading } = useQuickQuestions();
  const threadRuntime = useThreadRuntime();

  const handleQuickQuestion = (text: string) => {
    // Use simple string format which assistant-ui handles automatically
    threadRuntime.append(text);
  };

  // Fallback suggestions if API fails or is loading
  // These are phrased from the USER's perspective (what they would say/ask)
  const fallbackSuggestions = [
    {
      id: "1",
      text: "我想了解退休規劃，有什麼建議？",
      category: "retirement",
    },
    {
      id: "2",
      text: "幫我推薦適合的投資理財產品",
      category: "investment",
    },
    {
      id: "3",
      text: "我想評估自己的風險承受度",
      category: "risk",
    },
    {
      id: "4",
      text: "我想開始規劃我的財務目標",
      category: "planning",
    },
  ];

  const displayQuestions =
    questions.length > 0 ? questions : isLoading ? [] : fallbackSuggestions;

  if (isLoading) {
    return (
      <div className="aui-thread-welcome-suggestions grid w-full gap-3 pb-6 @md:grid-cols-2">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-20 animate-pulse rounded-2xl bg-muted/50"
            style={{ animationDelay: `${i * 100}ms` }}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="aui-thread-welcome-suggestions grid w-full gap-3 pb-6 @md:grid-cols-2">
      {displayQuestions.slice(0, 4).map((question, index) => {
        const Icon = categoryIcons[question.category] || SparklesIcon;

        return (
          <div
            key={question.id}
            className="aui-thread-welcome-suggestion-display animate-fade-in-up"
            style={{ animationDelay: `${400 + index * 100}ms` }}
          >
            <Button
              variant="ghost"
              onClick={() => handleQuickQuestion(question.text)}
              className="card-elevated group h-auto w-full flex-col items-start justify-start gap-2 rounded-2xl border border-border/50 bg-card px-5 py-4 text-left shadow-sm transition-all hover:border-amber-200 hover:bg-amber-50/50 dark:hover:border-amber-900 dark:hover:bg-amber-950/20"
              aria-label={question.text}
            >
              <div className="flex w-full items-start gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary transition-colors group-hover:bg-amber-100 dark:group-hover:bg-amber-900/30">
                  <Icon className="h-4 w-4 text-muted-foreground transition-colors group-hover:text-amber-600 dark:group-hover:text-amber-400" />
                </div>
                <span className="text-sm font-medium leading-relaxed text-foreground">
                  {question.text}
                </span>
              </div>
            </Button>
          </div>
        );
      })}
    </div>
  );
};

const Composer: FC = () => {
  return (
    <ComposerPrimitive.Root className="aui-composer-root relative flex w-full flex-col">
      <ComposerPrimitive.AttachmentDropzone className="aui-composer-attachment-dropzone flex w-full flex-col rounded-2xl border border-border/50 bg-card px-1 pt-2 shadow-lg outline-none transition-all has-[textarea:focus-visible]:border-amber-300 has-[textarea:focus-visible]:ring-2 has-[textarea:focus-visible]:ring-amber-200/50 data-[dragging=true]:border-amber-400 data-[dragging=true]:border-dashed data-[dragging=true]:bg-amber-50/50 dark:has-[textarea:focus-visible]:border-amber-700 dark:has-[textarea:focus-visible]:ring-amber-900/30">
        <ComposerAttachments />
        <ComposerPrimitive.Input
          placeholder="Tell me about your financial goals..."
          className="aui-composer-input mb-1 max-h-40 min-h-14 w-full resize-none bg-transparent px-4 pt-2 pb-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-0"
          rows={1}
          autoFocus
          aria-label="Message input"
        />
        <ComposerAction />
      </ComposerPrimitive.AttachmentDropzone>
    </ComposerPrimitive.Root>
  );
};

const ComposerAction: FC = () => {
  return (
    <div className="aui-composer-action-wrapper relative mx-2 mb-2 flex items-center justify-between">
      <ComposerAddAttachment />

      <AssistantIf condition={({ thread }) => !thread.isRunning}>
        <ComposerPrimitive.Send asChild>
          <TooltipIconButton
            tooltip="Send message"
            side="bottom"
            type="submit"
            variant="default"
            size="icon"
            className="aui-composer-send size-9 rounded-full bg-gradient-to-br from-amber-500 to-amber-600 shadow-md transition-all hover:from-amber-400 hover:to-amber-500 hover:shadow-lg"
            aria-label="Send message"
          >
            <SendHorizonalIcon className="aui-composer-send-icon size-4 text-white" />
          </TooltipIconButton>
        </ComposerPrimitive.Send>
      </AssistantIf>

      <AssistantIf condition={({ thread }) => thread.isRunning}>
        <ComposerPrimitive.Cancel asChild>
          <Button
            type="button"
            variant="default"
            size="icon"
            className="aui-composer-cancel size-9 rounded-full bg-muted text-muted-foreground hover:bg-destructive hover:text-destructive-foreground"
            aria-label="Stop generating"
          >
            <SquareIcon className="aui-composer-cancel-icon size-3 fill-current" />
          </Button>
        </ComposerPrimitive.Cancel>
      </AssistantIf>
    </div>
  );
};

const MessageError: FC = () => {
  return (
    <MessagePrimitive.Error>
      <ErrorPrimitive.Root className="aui-message-error-root mt-3 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-destructive text-sm dark:bg-destructive/5 dark:text-red-200">
        <ErrorPrimitive.Message className="aui-message-error-message line-clamp-2" />
      </ErrorPrimitive.Root>
    </MessagePrimitive.Error>
  );
};

const AssistantMessage: FC = () => {
  return (
    <MessagePrimitive.Root
      className="aui-assistant-message-root animate-fade-in-up relative mx-auto w-full max-w-(--thread-max-width) py-4"
      data-role="assistant"
    >
      <div className="flex gap-4">
        {/* Avatar */}
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-md">
          <SparklesIcon className="h-4 w-4 text-white" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="aui-assistant-message-content wrap-break-word rounded-2xl bg-card px-4 py-3 text-foreground leading-relaxed shadow-sm">
            <MessagePrimitive.Parts
              components={{
                Text: MarkdownText,
                tools: {
                  by_name: {
                    product_recommendation: ProductRecommendationTool,
                  },
                  Fallback: ToolFallback,
                },
              }}
            />
            <MessageError />
          </div>

          <div className="aui-assistant-message-footer mt-2 ml-2 flex">
            <BranchPicker />
            <AssistantActionBar />
          </div>
        </div>
      </div>
    </MessagePrimitive.Root>
  );
};

const AssistantActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      autohideFloat="single-branch"
      className="aui-assistant-action-bar-root col-start-3 row-start-2 -ml-1 flex gap-1 text-muted-foreground data-floating:absolute data-floating:rounded-xl data-floating:border data-floating:border-border/50 data-floating:bg-card data-floating:p-1 data-floating:shadow-lg"
    >
      <ActionBarPrimitive.Copy asChild>
        <TooltipIconButton tooltip="Copy">
          <AssistantIf condition={({ message }) => message.isCopied}>
            <CheckIcon />
          </AssistantIf>
          <AssistantIf condition={({ message }) => !message.isCopied}>
            <CopyIcon />
          </AssistantIf>
        </TooltipIconButton>
      </ActionBarPrimitive.Copy>
      <ActionBarPrimitive.Reload asChild>
        <TooltipIconButton tooltip="Regenerate">
          <RefreshCwIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Reload>
      <ActionBarMorePrimitive.Root>
        <ActionBarMorePrimitive.Trigger asChild>
          <TooltipIconButton
            tooltip="More"
            className="data-[state=open]:bg-accent"
          >
            <MoreHorizontalIcon />
          </TooltipIconButton>
        </ActionBarMorePrimitive.Trigger>
        <ActionBarMorePrimitive.Content
          side="bottom"
          align="start"
          className="aui-action-bar-more-content z-50 min-w-36 overflow-hidden rounded-xl border border-border/50 bg-card p-1 text-popover-foreground shadow-lg"
        >
          <ActionBarPrimitive.ExportMarkdown asChild>
            <ActionBarMorePrimitive.Item className="aui-action-bar-more-item flex cursor-pointer select-none items-center gap-2 rounded-lg px-3 py-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground">
              <DownloadIcon className="size-4" />
              Export as Markdown
            </ActionBarMorePrimitive.Item>
          </ActionBarPrimitive.ExportMarkdown>
        </ActionBarMorePrimitive.Content>
      </ActionBarMorePrimitive.Root>
    </ActionBarPrimitive.Root>
  );
};

const UserMessage: FC = () => {
  return (
    <MessagePrimitive.Root
      className="aui-user-message-root animate-fade-in-up mx-auto grid w-full max-w-(--thread-max-width) auto-rows-auto grid-cols-[minmax(72px,1fr)_auto] content-start gap-y-2 px-2 py-4 [&:where(>*)]:col-start-2"
      data-role="user"
    >
      <UserMessageAttachments />

      <div className="aui-user-message-content-wrapper relative col-start-2 min-w-0">
        <div className="aui-user-message-content wrap-break-word rounded-2xl bg-primary px-4 py-3 text-primary-foreground shadow-md">
          <MessagePrimitive.Parts />
        </div>
        <div className="aui-user-action-bar-wrapper absolute top-1/2 left-0 -translate-x-full -translate-y-1/2 pr-2">
          <UserActionBar />
        </div>
      </div>

      <BranchPicker className="aui-user-branch-picker col-span-full col-start-1 row-start-3 -mr-1 justify-end" />
    </MessagePrimitive.Root>
  );
};

const UserActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="aui-user-action-bar-root flex flex-col items-end"
    >
      <ActionBarPrimitive.Edit asChild>
        <TooltipIconButton tooltip="Edit" className="aui-user-action-edit p-4">
          <PencilIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Edit>
    </ActionBarPrimitive.Root>
  );
};

const EditComposer: FC = () => {
  return (
    <MessagePrimitive.Root className="aui-edit-composer-wrapper mx-auto flex w-full max-w-(--thread-max-width) flex-col px-2 py-4">
      <ComposerPrimitive.Root className="aui-edit-composer-root ml-auto flex w-full max-w-[85%] flex-col rounded-2xl bg-muted shadow-sm">
        <ComposerPrimitive.Input
          className="aui-edit-composer-input min-h-14 w-full resize-none bg-transparent p-4 text-foreground text-sm outline-none"
          autoFocus
        />
        <div className="aui-edit-composer-footer mx-3 mb-3 flex items-center gap-2 self-end">
          <ComposerPrimitive.Cancel asChild>
            <Button variant="ghost" size="sm">
              Cancel
            </Button>
          </ComposerPrimitive.Cancel>
          <ComposerPrimitive.Send asChild>
            <Button
              size="sm"
              className="bg-gradient-to-br from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500"
            >
              Update
            </Button>
          </ComposerPrimitive.Send>
        </div>
      </ComposerPrimitive.Root>
    </MessagePrimitive.Root>
  );
};

const BranchPicker: FC<BranchPickerPrimitive.Root.Props> = ({
  className,
  ...rest
}) => {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className={cn(
        "aui-branch-picker-root mr-2 -ml-2 inline-flex items-center text-muted-foreground text-xs",
        className
      )}
      {...rest}
    >
      <BranchPickerPrimitive.Previous asChild>
        <TooltipIconButton tooltip="Previous">
          <ChevronLeftIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Previous>
      <span className="aui-branch-picker-state font-mono font-medium tabular-nums">
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <TooltipIconButton tooltip="Next">
          <ChevronRightIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  );
};
