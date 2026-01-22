"use client";

/**
 * FinancialGoalCard - Displays user's financial goal extracted from conversation.
 * Only renders when at least one goal field has data.
 */

import { Card, CardContent } from "@/components/ui/card";
import { CakeIcon, WalletIcon, ClockIcon, TargetIcon } from "lucide-react";
import type { FinancialGoal } from "@/lib/types";

interface FinancialGoalCardProps {
  goal: FinancialGoal | null;
}

const goalTypeLabels: Record<string, string> = {
  retirement: "Retirement",
  wealth_growth: "Wealth Growth",
  education: "Education",
  house: "Home Purchase",
};

export function FinancialGoalCard({ goal }: FinancialGoalCardProps) {
  if (!goal) {
    return null;
  }

  const hasAnyData =
    goal.target_age || goal.target_amount || goal.timeline || goal.goal_type;

  if (!hasAnyData) {
    return null;
  }

  return (
    <Card className="border-0 bg-card shadow-sm">
      <CardContent className="pt-4 space-y-3">
        <div className="flex items-center gap-2">
          <TargetIcon className="h-4 w-4 text-amber-500" />
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Financial Goal
          </p>
        </div>

        <div className="grid gap-3">
          {/* Target Age */}
          {goal.target_age && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <CakeIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Target Age</p>
                <p className="text-sm font-medium">{goal.target_age} years old</p>
              </div>
            </div>
          )}

          {/* Target Amount */}
          {goal.target_amount && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <WalletIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Target Amount</p>
                <p className="text-sm font-medium">{goal.target_amount}</p>
              </div>
            </div>
          )}

          {/* Timeline */}
          {goal.timeline && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <ClockIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Timeline</p>
                <p className="text-sm font-medium">{goal.timeline}</p>
              </div>
            </div>
          )}

          {/* Goal Type */}
          {goal.goal_type && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <TargetIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Goal Type</p>
                <p className="text-sm font-medium">
                  {goalTypeLabels[goal.goal_type] || goal.goal_type}
                </p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
