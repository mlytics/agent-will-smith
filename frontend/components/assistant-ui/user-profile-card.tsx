"use client";

/**
 * UserProfileCard - Displays user profile information extracted from conversation.
 * Only shows fields that have values.
 */

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  UserIcon,
  ShieldIcon,
  TrendingUpIcon,
  TargetIcon,
  WalletIcon,
  GraduationCapIcon,
} from "lucide-react";
import type { IntentProfile } from "@/lib/types";

interface UserProfileCardProps {
  profile: IntentProfile;
}

const lifeStageLabels: Record<string, string> = {
  early_career: "Early Career",
  mid_career: "Mid Career",
  pre_retirement: "Pre-Retirement",
  retired: "Retired",
};

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

const experienceLabels: Record<string, string> = {
  beginner: "Beginner",
  intermediate: "Intermediate",
  experienced: "Experienced",
};

export function UserProfileCard({ profile }: UserProfileCardProps) {
  const hasAnyData =
    profile.life_stage ||
    profile.risk_preference ||
    profile.investment_experience ||
    profile.current_assets;

  if (!hasAnyData) {
    return null;
  }

  const RiskIcon = profile.risk_preference ? riskIcons[profile.risk_preference] : null;

  return (
    <Card className="border-0 bg-card shadow-sm">
      <CardContent className="pt-4 space-y-3">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          User Profile
        </p>

        <div className="grid gap-3">
          {/* Life Stage */}
          {profile.life_stage && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <UserIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Life Stage</p>
                <p className="text-sm font-medium">
                  {lifeStageLabels[profile.life_stage] || profile.life_stage}
                </p>
              </div>
            </div>
          )}

          {/* Risk Preference */}
          {profile.risk_preference && RiskIcon && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <RiskIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Risk Tolerance</p>
                <Badge
                  variant="secondary"
                  className={`${riskColors[profile.risk_preference]} border-0 font-medium capitalize text-xs`}
                >
                  {profile.risk_preference}
                </Badge>
              </div>
            </div>
          )}

          {/* Investment Experience */}
          {profile.investment_experience && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <GraduationCapIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Experience</p>
                <p className="text-sm font-medium">
                  {experienceLabels[profile.investment_experience] || profile.investment_experience}
                </p>
              </div>
            </div>
          )}

          {/* Current Assets */}
          {profile.current_assets && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary">
                <WalletIcon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Assets</p>
                <p className="text-sm font-medium">{profile.current_assets}</p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
