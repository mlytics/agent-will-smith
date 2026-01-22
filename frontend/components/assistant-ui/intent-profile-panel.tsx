"use client";

/**
 * IntentProfilePanel - Shows the user's evolving intent profile
 * with User Profile, Financial Goal, Signal History, and Session Stats.
 */

import { useIntentProfile } from "@/lib/intent-profile-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SparklesIcon } from "lucide-react";
import { UserProfileCard } from "./user-profile-card";
import { FinancialGoalCard } from "./financial-goal-card";
import { SignalHistory } from "./signal-history";
import { SessionStats } from "./session-stats";

export function IntentProfilePanel() {
  const { profile, turnCount } = useIntentProfile();
  const intentPercentage = Math.round(profile.intent_score * 100);

  const hasProfileData =
    profile.life_stage ||
    profile.risk_preference ||
    profile.investment_experience ||
    profile.current_assets ||
    profile.financial_goal ||
    profile.product_interests.length > 0;

  return (
    <div className="flex flex-col h-full">
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto space-y-5 p-1">
        {/* Header */}
        <div className="flex items-center gap-3 px-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg">
            <SparklesIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Your Profile</h2>
            <p className="text-xs text-muted-foreground">
              Insights from our conversation
            </p>
          </div>
        </div>

        {/* Intent Score Card */}
        <Card className="overflow-hidden border-0 bg-gradient-to-br from-card to-secondary/30 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-sm font-medium text-muted-foreground">
              <span>Intent Clarity</span>
              <span className="font-mono text-2xl font-bold text-foreground tabular-nums">
                {intentPercentage}%
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="intent-progress absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${intentPercentage}%` }}
              />
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              {intentPercentage < 30 && "Let's learn more about your goals"}
              {intentPercentage >= 30 &&
                intentPercentage < 60 &&
                "Building a clearer picture of your needs"}
              {intentPercentage >= 60 &&
                intentPercentage < 80 &&
                "Good understanding of your preferences"}
              {intentPercentage >= 80 && "Ready for personalized recommendations"}
            </p>
          </CardContent>
        </Card>

        {/* User Profile Card */}
        <UserProfileCard profile={profile} />

        {/* Financial Goal Card */}
        <FinancialGoalCard goal={profile.financial_goal} />

        {/* Product Interests */}
        {profile.product_interests.length > 0 && (
          <Card className="border-0 bg-card shadow-sm">
            <CardContent className="pt-4">
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Interests
              </p>
              <div className="flex flex-wrap gap-2">
                {profile.product_interests.map((interest) => (
                  <Badge
                    key={interest}
                    variant="outline"
                    className="border-border/50 bg-secondary/50 font-normal capitalize"
                  >
                    {interest.replace(/_/g, " ")}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Signal History */}
        <SignalHistory signals={profile.signals} />

        {/* Empty State */}
        {!hasProfileData && profile.signals.length === 0 && (
          <div className="rounded-xl border border-dashed border-border/50 bg-muted/30 p-6 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
              <SparklesIcon className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground">Share your story</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Tell me about your financial goals and I'll help build your profile
            </p>
          </div>
        )}
      </div>

      {/* Fixed footer */}
      <SessionStats turnCount={turnCount} signalCount={profile.signals.length} />
    </div>
  );
}
