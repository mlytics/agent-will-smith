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
};

interface IntentProfileContextType {
  profile: IntentProfile;
  updateProfile: (profile: IntentProfile) => void;
  resetProfile: () => void;
}

const IntentProfileContext = createContext<IntentProfileContextType | null>(null);

export function IntentProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<IntentProfile>(defaultProfile);

  const updateProfile = useCallback((newProfile: IntentProfile) => {
    setProfile(newProfile);
  }, []);

  const resetProfile = useCallback(() => {
    setProfile(defaultProfile);
  }, []);

  return (
    <IntentProfileContext.Provider value={{ profile, updateProfile, resetProfile }}>
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
