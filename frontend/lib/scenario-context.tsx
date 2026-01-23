"use client";

/**
 * Context for managing the selected scenario state across the application.
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { SCENARIOS, type Scenario } from "./scenarios";

interface ScenarioContextType {
  selectedScenario: Scenario;
  setScenario: (scenarioId: string) => void;
  resetScenario: () => void;
}

const defaultScenario = SCENARIOS.find((s) => s.id === "free_form")!;

const ScenarioContext = createContext<ScenarioContextType | null>(null);

export function ScenarioProvider({ children }: { children: ReactNode }) {
  const [selectedScenario, setSelectedScenario] =
    useState<Scenario>(defaultScenario);

  const setScenario = useCallback((scenarioId: string) => {
    const scenario = SCENARIOS.find((s) => s.id === scenarioId);
    if (scenario) {
      setSelectedScenario(scenario);
    }
  }, []);

  const resetScenario = useCallback(() => {
    setSelectedScenario(defaultScenario);
  }, []);

  return (
    <ScenarioContext.Provider
      value={{ selectedScenario, setScenario, resetScenario }}
    >
      {children}
    </ScenarioContext.Provider>
  );
}

/**
 * Hook to access the scenario context.
 * @throws Error if used outside of ScenarioProvider
 */
export function useScenario() {
  const context = useContext(ScenarioContext);
  if (!context) {
    throw new Error("useScenario must be used within ScenarioProvider");
  }
  return context;
}
