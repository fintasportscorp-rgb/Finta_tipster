import { Fragment } from "react";
import type { Match } from "../types";
import {
  SOURCES,
  scoreColor,
  absColor,
  validityColor,
  leagueBadge,
  formScore,
  getValueEdge,
} from "../lib/format";
import FormBoxes from "./FormBoxes";
import ExpandedMatch from "./ExpandedMatch";

export type SortKey =
  | "league" | "date" | "home_team" | "home_score" | "home_form" | "home_abs"
  | "away_score" | "away_form" | "away_abs" | "away_team" | "odds" | "validity"
  | "value_home" | "value_away";

function sortValue(m: Match, key: SortKey): string | number | null {
  switch (key) {
    case "league": return m.league;
    case "date": return m.date_short;
    case "home_team": return m.home.team;
    case "home_score": return m.home.score;
    case "home_form": return formScore(m.home.form_string);
    case "home_abs": return m.home.absent_count;
    case "away_score": return m.away.score;
    case "away_form": return formScore(m.away.form_string);
    case "away_abs": return m.away.absent_count;
    case "away_team": return m.away.team;
    case "odds": return m.odds.home || 0;
    case "validity": return m.validity;
    case "value_home": return getValueEdge(m, "home");
    case "value_away": return getValueEdge(m, "away");
    default: return 0;
  }
}

// Column visibility: some columns collapse below 600px (detail lives in expanded row).
const HIDE_SM = "hidden min-[600px]:table-cell";

function ValueCell({ m, side }: { m: Match; side: "home" | "away" }) {
  const edge = getValueEdge(m, side);
  if (edge === null) return <span className="text-dimmer text-[11px]">—</span>;
  const vbs = (m.value_bets || []).filter((v) => v.side === side);
  if (!vbs.length) return <span className="text-dimmer text-[11px]">—</span>;
  return (
    <>
      {vbs.map((v, i) => {
        const cls =
          v.edge >= 15
            ? "bg-good/20 text-good border-good/30"
            : v.edge >= 10
              ? "bg-warn/20 text-warn border-warn/30"
              : "bg-accent/15 text-accent border-accent/25";
        return (
          <span
            key={i}
            title={`${v.team} @ ${v.odds} — Form: ${v.form_prob}% vs Implied: ${v.implied_prob}%`}
            className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold border m-px ${cls}`}
          >
            +{v.edge}%
          </span>
        );
      })}
    </>
  );
}

export default function MatchTable({
  matches,
  sortKey,
  sortDir,
  onSort,
  selectedId,
  onToggle,
  rollingWindow,
}: {
  matches: Match[];
  sortKey: SortKey | null;
  sortDir: number;
  onSort: (k: SortKey) => void;
  selectedId: string | number | null;
  onToggle: (id: string | number) => void;
  rollingWindow: number;
}) {
  const sorted = [...matches];
  if (sortKey) {
    sorted.sort((a, b) => {
      const va = sortValue(a, sortKey);
      const vb = sortValue(b, sortKey);
      if (va === null && vb === null) return 0;
      if (va === null) return 1;
      if (vb === null) return -1;
      if (typeof va === "string" && typeof vb === "string") return va.localeCompare(vb) * sortDir;
      return (((va as number) || 0) - ((vb as number) || 0)) * sortDir;
    });
  }

  const Th = ({ k, label, cls = "" }: { k: SortKey; label: string; cls?: string }) => (
    <th
      onClick={() => onSort(k)}
      className={`px-2 py-2.5 text-left text-[10px] uppercase tracking-wide font-normal border-b-2 border-border whitespace-nowrap cursor-pointer select-none sticky top-0 bg-bg z-10 ${
        sortKey === k ? "text-accent" : "text-dim hover:text-text"
      } ${cls}`}
    >
      {label}
      {sortKey === k && <span className="text-[9px] ml-0.5">{sortDir > 0 ? "↑" : "↓"}</span>}
    </th>
  );

  return (
    <div className="scroll-x">
      <table className="w-full border-separate border-spacing-0 text-[13px] max-[768px]:text-[11px]">
        <thead>
          <tr>
            <Th k="league" label="League" />
            <Th k="date" label="Date" cls={HIDE_SM} />
            <Th k="home_team" label="Home" />
            <Th k="home_score" label="Score" />
            <Th k="home_form" label="Form" cls={HIDE_SM} />
            <Th k="home_abs" label="Abs" cls={HIDE_SM} />
            <Th k="away_score" label="Score" />
            <Th k="away_form" label="Form" cls={HIDE_SM} />
            <Th k="away_abs" label="Abs" cls={HIDE_SM} />
            <Th k="away_team" label="Away" />
            <Th k="odds" label="Odds" />
            <Th k="validity" label="Sources" cls={HIDE_SM} />
            <Th k="value_home" label="Val H" />
            <Th k="value_away" label="Val A" />
          </tr>
        </thead>
        <tbody>
          {sorted.map((m) => {
            const selected = m.id === selectedId;
            const oddsTxt = m.odds.home ? (
              <>
                <span className="text-accent font-semibold">{m.odds.home}</span> / {m.odds.away}
              </>
            ) : (
              "—"
            );
            return (
              <Fragment key={m.id}>
                <tr
                  onClick={() => onToggle(m.id)}
                  className={`cursor-pointer transition hover:bg-card ${selected ? "bg-card2" : ""}`}
                >
                  <td className="px-2 py-2.5 border-b border-border align-middle">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold whitespace-nowrap ${leagueBadge(m.league)}`}>
                      {m.league}
                    </span>
                  </td>
                  <td className={`px-2 py-2.5 border-b border-border text-dim text-xs whitespace-nowrap ${HIDE_SM}`}>
                    {m.date_short}
                  </td>
                  <td className="px-2 py-2.5 border-b border-border font-semibold whitespace-nowrap">
                    {m.home.team}
                  </td>
                  <td className={`px-2 py-2.5 border-b border-border font-extrabold text-center text-lg max-[768px]:text-[15px] ${scoreColor(m.home.score)}`}>
                    {Math.round(m.home.score)}
                  </td>
                  <td className={`px-2 py-2.5 border-b border-border ${HIDE_SM}`}>
                    <FormBoxes form={m.home.form_string} mini />
                  </td>
                  <td className={`px-2 py-2.5 border-b border-border text-center text-[11px] ${HIDE_SM}`}>
                    <span className={`px-1.5 py-0.5 rounded font-semibold ${absColor(m.home.absent_count)}`}>
                      {m.home.absent_count}
                    </span>
                  </td>
                  <td className={`px-2 py-2.5 border-b border-border font-extrabold text-center text-lg max-[768px]:text-[15px] ${scoreColor(m.away.score)}`}>
                    {Math.round(m.away.score)}
                  </td>
                  <td className={`px-2 py-2.5 border-b border-border ${HIDE_SM}`}>
                    <FormBoxes form={m.away.form_string} mini />
                  </td>
                  <td className={`px-2 py-2.5 border-b border-border text-center text-[11px] ${HIDE_SM}`}>
                    <span className={`px-1.5 py-0.5 rounded font-semibold ${absColor(m.away.absent_count)}`}>
                      {m.away.absent_count}
                    </span>
                  </td>
                  <td className="px-2 py-2.5 border-b border-border font-semibold text-right whitespace-nowrap">
                    {m.away.team}
                  </td>
                  <td className="px-2 py-2.5 border-b border-border text-center text-xs text-dim whitespace-nowrap">
                    {oddsTxt}
                  </td>
                  <td className={`px-2 py-2.5 border-b border-border ${HIDE_SM}`}>
                    <div className="flex items-center gap-1.5">
                      <div className="flex gap-[3px]">
                        {SOURCES.map((s) => (
                          <div
                            key={s.key}
                            title={s.label}
                            className={`w-[7px] h-[7px] rounded-full ${m.sources?.[s.key] ? "bg-good" : "bg-border"}`}
                          />
                        ))}
                      </div>
                      <span className={`text-[11px] font-bold ${validityColor(m.validity, m.validity_total)}`}>
                        {m.validity}/{m.validity_total}
                      </span>
                    </div>
                  </td>
                  <td className="px-2 py-2.5 border-b border-border text-center whitespace-nowrap">
                    <ValueCell m={m} side="home" />
                  </td>
                  <td className="px-2 py-2.5 border-b border-border text-center whitespace-nowrap">
                    <ValueCell m={m} side="away" />
                  </td>
                </tr>
                {selected && (
                  <tr>
                    <td colSpan={14} className="p-0 border-b border-border bg-card">
                      <ExpandedMatch m={m} rollingWindow={rollingWindow} />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
