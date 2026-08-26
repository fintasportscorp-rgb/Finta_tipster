import { useMemo } from "react";
import { BarChart3, Coins, LayoutGrid } from "lucide-react";
import type { Match } from "@/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TooltipProvider } from "@/components/ui/tooltip";
import TeamSummary from "./TeamSummary";
import FormMatchesTable from "./FormMatchesTable";
import AbsencesList from "./AbsencesList";
import XgChart from "./XgChart";
import GoalTimingChart from "./GoalTimingChart";
import FormationsList from "./FormationsList";
import H2HPanel from "./H2HPanel";
import OddsMarkets from "./OddsMarkets";
import ValueBetsPanel from "./ValueBetsPanel";
import TipsPanel from "./TipsPanel";

export default function MatchDetail({
  m,
  rollingWindow,
  compact = false,
}: {
  m: Match;
  rollingWindow: number;
  compact?: boolean;
}) {
  const weights = useMemo<Record<string, number>>(
    () => ({ results: 0.25, xg: 0.2, availability: 0.2, formation: 0.1, odds: 0.15, tips: 0.1 }),
    [],
  );

  return (
    <TooltipProvider delayDuration={150}>
      <div className={compact ? "px-3 py-4 sm:px-4" : "p-4 sm:p-5"}>
        <Tabs defaultValue="overview">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview" className="!text-xs sm:!text-sm">
              <LayoutGrid className="!size-3.5" /> Overview
            </TabsTrigger>
            <TabsTrigger value="stats" className="!text-xs sm:!text-sm">
              <BarChart3 className="!size-3.5" /> Stats
            </TabsTrigger>
            <TabsTrigger value="market" className="!text-xs sm:!text-sm">
              <Coins className="!size-3.5" /> Market
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4 outline-none">
            <div className="grid gap-3 sm:grid-cols-2">
              <TeamSummary t={m.home} weights={weights} />
              <TeamSummary t={m.away} weights={weights} />
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <FormMatchesTable team={m.home.team} matches={m.home.form_matches} />
              <FormMatchesTable team={m.away.team} matches={m.away.form_matches} />
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <AbsencesList team={m.home.team} absences={m.home.absences} />
              <AbsencesList team={m.away.team} absences={m.away.absences} />
            </div>
          </TabsContent>

          <TabsContent value="stats" className="space-y-4 outline-none">
            <GoalTimingChart gt={m.goal_timing} homeTeam={m.home_team} awayTeam={m.away_team} />
            <div className="grid gap-4 lg:grid-cols-2">
              <XgChart team={m.home.team} data={m.home.xg_rolling} window={rollingWindow} />
              <XgChart team={m.away.team} data={m.away.xg_rolling} window={rollingWindow} />
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <FormationsList
                team={m.home.team}
                hist={m.home.formation_history}
                radicalChanges={m.home.radical_changes}
              />
              <FormationsList
                team={m.away.team}
                hist={m.away.formation_history}
                radicalChanges={m.away.radical_changes}
              />
            </div>
            <H2HPanel h2h={m.h2h} homeTeam={m.home_team} awayTeam={m.away_team} />
          </TabsContent>

          <TabsContent value="market" className="space-y-4 outline-none">
            <OddsMarkets m={m} />
            <ValueBetsPanel vbs={m.value_bets} />
            <TipsPanel tips={m.tips} />
          </TabsContent>
        </Tabs>
      </div>
    </TooltipProvider>
  );
}
