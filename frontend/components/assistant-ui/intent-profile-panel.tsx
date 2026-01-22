"use client";

/**
 * Intent Profile Panel - Shows the user's evolving intent profile
 * in a visually distinctive sidebar with sophisticated styling.
 */

import { useIntentProfile } from "@/lib/intent-profile-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  TrendingUpIcon,
  ShieldIcon,
  TargetIcon,
  SparklesIcon,
  UserIcon,
} from "lucide-react";

const riskIcons = {
  conservative: ShieldIcon,
  moderate: TargetIcon,
  aggressive: TrendingUpIcon,
};

const riskColors = {
  conservative: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  moderate: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  aggressive: "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300",
};

export function IntentProfilePanel() {
  const { profile } = useIntentProfile();
  const intentPercentage = Math.round(profile.intent_score * 100);

  const RiskIcon = profile.risk_preference
    ? riskIcons[profile.risk_preference]
    : null;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3 px-1">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-lg">
          <SparklesIcon className="h-5 w-5 text-white" />
        </div>
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            Your Profile
          </h2>
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

      {/* Life Stage */}
      {profile.life_stage && (
        <Card className="border-0 bg-card shadow-sm card-elevated">
          <CardContent className="pt-4">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <UserIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Life Stage
                </p>
                <p className="font-semibold capitalize leading-tight">
                  {profile.life_stage.replace(/_/g, " ")}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Risk Preference */}
      {profile.risk_preference && RiskIcon && (
        <Card className="border-0 bg-card shadow-sm card-elevated">
          <CardContent className="pt-4">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <RiskIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Risk Tolerance
                </p>
                <Badge
                  variant="secondary"
                  className={`${riskColors[profile.risk_preference]} border-0 font-medium capitalize`}
                >
                  {profile.risk_preference}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Product Interests */}
      {profile.product_interests.length > 0 && (
        <Card className="border-0 bg-card shadow-sm card-elevated">
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

      {/* Empty State */}
      {!profile.life_stage &&
        !profile.risk_preference &&
        profile.product_interests.length === 0 && (
          <div className="rounded-xl border border-dashed border-border/50 bg-muted/30 p-6 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
              <SparklesIcon className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground">
              Share your story
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Tell me about your financial goals and I'll help build your
              profile
            </p>
          </div>
        )}
    </div>
  );
}
