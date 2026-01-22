"use client";

/**
 * Context for managing the intent profile state across the application.
 */

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { IntentProfile } from "./types";

const defaultProfile: IntentProfile = {
  life_stage: null,
  risk_preference: null,
  product_interests: [],
  intent_score: 0,
  signals: [],
  financial_goal: null,
  current_assets: null,
  investment_experience: null,
};

interface IntentProfileContextType {
  profile: IntentProfile;
  updateProfile: (profile: IntentProfile) => void;
  resetProfile: () => void;
  /** Number of conversation turns (user messages) */
  turnCount: number;
  incrementTurnCount: () => void;
}

const IntentProfileContext = createContext<IntentProfileContextType | null>(null);

export function IntentProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<IntentProfile>(defaultProfile);
  const [turnCount, setTurnCount] = useState(0);

  const updateProfile = useCallback((newProfile: IntentProfile) => {
    setProfile(newProfile);
  }, []);

  const resetProfile = useCallback(() => {
    setProfile(defaultProfile);
    setTurnCount(0);
  }, []);

  const incrementTurnCount = useCallback(() => {
    setTurnCount((prev) => prev + 1);
  }, []);

  return (
    <IntentProfileContext.Provider
      value={{ profile, updateProfile, resetProfile, turnCount, incrementTurnCount }}
    >
      {children}
    </IntentProfileContext.Provider>
  );
}

export function useIntentProfile() {
  const context = useContext(IntentProfileContext);
  if (!context) {
    throw new Error("useIntentProfile must be used within IntentProfileProvider");
  }
  return context;
}
