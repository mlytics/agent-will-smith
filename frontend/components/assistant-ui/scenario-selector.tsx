"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDownIcon, FlaskConicalIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useScenario } from "@/lib/scenario-context";
import { SCENARIOS, type Scenario } from "@/lib/scenarios";

function ScenarioCard({
  scenario,
  isSelected,
  onSelect,
}: {
  scenario: Scenario;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Card
            className={cn(
              "cursor-pointer p-3 transition-all hover:shadow-md",
              "flex flex-col items-center text-center gap-1 min-w-[100px]",
              isSelected
                ? "ring-2 ring-amber-500 bg-amber-50 dark:bg-amber-950/30"
                : "hover:bg-secondary/50"
            )}
            onClick={onSelect}
          >
            <span className="text-2xl">{scenario.icon}</span>
            <span className="text-xs font-medium leading-tight">
              {scenario.name}
            </span>
            <span className="text-[10px] text-muted-foreground leading-tight">
              {scenario.shortDesc}
            </span>
          </Card>
        </TooltipTrigger>
        {scenario.persona && (
          <TooltipContent side="bottom" className="max-w-xs">
            <p className="text-xs whitespace-pre-line">{scenario.persona}</p>
          </TooltipContent>
        )}
      </Tooltip>
    </TooltipProvider>
  );
}

export function ScenarioSelector() {
  const [isOpen, setIsOpen] = useState(true);
  const { selectedScenario, setScenario } = useScenario();

  // Split scenarios: main row (4) + second row (1: free_form)
  const mainScenarios = SCENARIOS.filter((s) => s.id !== "free_form");
  const freeFormScenario = SCENARIOS.find((s) => s.id === "free_form")!;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <div className="flex items-center justify-between px-2 py-2 cursor-pointer hover:bg-secondary/30 rounded-lg transition-colors">
          <div className="flex items-center gap-2">
            <FlaskConicalIcon className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">測試情境</span>
            <span className="text-xs text-muted-foreground">
              {selectedScenario.name}
            </span>
          </div>
          <ChevronDownIcon
            className={cn(
              "h-4 w-4 text-muted-foreground transition-transform",
              isOpen && "rotate-180"
            )}
          />
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div className="pt-2 pb-4 space-y-3">
          {/* Main scenarios row */}
          <div className="flex flex-wrap gap-2 justify-center">
            {mainScenarios.map((scenario) => (
              <ScenarioCard
                key={scenario.id}
                scenario={scenario}
                isSelected={selectedScenario.id === scenario.id}
                onSelect={() => setScenario(scenario.id)}
              />
            ))}
          </div>

          {/* Free form centered below */}
          <div className="flex justify-center">
            <ScenarioCard
              scenario={freeFormScenario}
              isSelected={selectedScenario.id === freeFormScenario.id}
              onSelect={() => setScenario(freeFormScenario.id)}
            />
          </div>

          {/* Persona hint if selected */}
          {selectedScenario.persona && (
            <div className="mx-auto max-w-md p-3 rounded-lg bg-secondary/50 text-xs text-muted-foreground">
              <p className="font-medium text-foreground mb-1">角色設定：</p>
              <p className="whitespace-pre-line">{selectedScenario.persona}</p>
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
