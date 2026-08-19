import type { Match } from "../types";
import TeamBlock from "./TeamBlock";
import FormMatches from "./FormMatches";
import H2H from "./H2H";
import XgSpark from "./XgSpark";
import Formations from "./Formations";
import Absences from "./Absences";
import OddsTable from "./OddsTable";
import ValueBets from "./ValueBets";
import Tips from "./Tips";

function Title({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[11px] uppercase tracking-wider text-dim mb-2 mt-3">{children}</div>
  );
}

export default function ExpandedMatch({ m, rollingWindow }: { m: Match; rollingWindow: number }) {
  const h = m.home;
  const a = m.away;
  return (
    <div className="p-3 sm:p-5 grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 bg-card">
      <div className="col-span-full text-center mb-1">
        <span className="text-dim text-xs">
          {m.league} · GW {m.gameweek || "?"} · {m.datetime}
        </span>
      </div>

      <div className="col-span-full grid grid-cols-[1fr_auto_1fr] gap-2 sm:gap-3 items-stretch">
        <TeamBlock t={h} />
        <div className="flex items-center text-dim font-bold text-base">VS</div>
        <TeamBlock t={a} />
      </div>

      <div>
        <Title>Form Matches ({h.team})</Title>
        <FormMatches t={h} />
      </div>
      <div>
        <Title>Form Matches ({a.team})</Title>
        <FormMatches t={a} />
      </div>

      <div className="col-span-full">
        <Title>Head to Head</Title>
        <H2H h2h={m.h2h} homeTeam={m.home_team} awayTeam={m.away_team} />
      </div>

      <div>
        <Title>xG Rolling ({rollingWindow})</Title>
        <div className="text-xs text-accent mb-1">{h.team}</div>
        <XgSpark data={h.xg_rolling} />
      </div>
      <div>
        <Title>xG Rolling ({rollingWindow})</Title>
        <div className="text-xs text-accent mb-1">{a.team}</div>
        <XgSpark data={a.xg_rolling} />
      </div>

      <div>
        <Title>Formations ({h.radical_changes} changes)</Title>
        <Formations hist={h.formation_history} />
      </div>
      <div>
        <Title>Formations ({a.radical_changes} changes)</Title>
        <Formations hist={a.formation_history} />
      </div>

      <div>
        <Title>Absences ({h.absent_count})</Title>
        <Absences absences={h.absences} />
      </div>
      <div>
        <Title>Absences ({a.absent_count})</Title>
        <Absences absences={a.absences} />
      </div>

      <div className="col-span-full">
        <Title>Odds</Title>
        <OddsTable m={m} />
      </div>
      <div className="col-span-full">
        <Title>Value Bets</Title>
        <ValueBets vbs={m.value_bets} />
      </div>
      <div className="col-span-full">
        <Title>Expert Tips ({(m.tips || []).length})</Title>
        <Tips tips={m.tips} />
      </div>
    </div>
  );
}
