import type { Match, SourceKey } from "../types";

export const METRICS: { key: keyof Match["home"]["components"]; label: string; w: string }[] = [
  { key: "results", label: "Results", w: "25%" },
  { key: "xg", label: "xG", w: "20%" },
  { key: "availability", label: "Avail", w: "20%" },
  { key: "formation", label: "Form", w: "10%" },
  { key: "odds", label: "Odds", w: "15%" },
  { key: "tips", label: "Tips", w: "10%" },
];

export const SOURCES: { key: SourceKey; label: string }[] = [
  { key: "results", label: "Results" },
  { key: "xg", label: "xG" },
  { key: "availability", label: "Absences" },
  { key: "formation", label: "Formation" },
  { key: "odds", label: "Odds" },
  { key: "tips", label: "Tipsters" },
  { key: "h2h", label: "H2H" },
];

export function scoreColor(s: number): string {
  return s >= 70 ? "text-good" : s >= 50 ? "text-warn" : "text-bad";
}
export function fillColor(v: number): string {
  return v >= 60 ? "bg-good" : v >= 40 ? "bg-warn" : "bg-bad";
}
export function absColor(n: number): string {
  return n === 0 ? "text-dimmer" : n <= 3 ? "bg-warn/15 text-warn" : "bg-bad/15 text-bad";
}
export function validityColor(n: number, total: number): string {
  return n >= total * 0.7 ? "text-good" : n >= total * 0.4 ? "text-warn" : "text-bad";
}

const LEAGUE_COLORS: Record<string, string> = {
  "Serie A": "text-[#4d9fff] bg-[#0078ff26]",
  "Premier League": "text-[#ef3e2f] bg-[#ef3e2b26]",
  "La Liga": "text-[#ff8c00] bg-[#ff8c0026]",
  Bundesliga: "text-[#dc0000] bg-[#dc000026]",
  "Ligue 1": "text-[#b400dc] bg-[#b400dc26]",
};
export function leagueBadge(l: string): string {
  return LEAGUE_COLORS[l] ?? "text-dim bg-card2";
}

export function formScore(formString: string[] | undefined): number {
  if (!formString || formString.length === 0) return 0;
  let s = 0;
  for (const r of formString) {
    if (r === "W") s += 3;
    else if (r === "D") s += 1;
  }
  return s;
}

const VB_SCORE_THRESHOLD = 50;
const VB_SOURCE_THRESHOLD = 4;
const VB_SCORE_GAP = 20;

export function getValueEdge(m: Match, side: "home" | "away"): number | null {
  const score = side === "home" ? m.home.score : m.away.score;
  const oppScore = side === "home" ? m.away.score : m.home.score;
  if (score < VB_SCORE_THRESHOLD || m.validity < VB_SOURCE_THRESHOLD) return null;
  if (score < oppScore - VB_SCORE_GAP) return null;
  const vbs = m.value_bets;
  if (!vbs || vbs.length === 0) return null;
  const filtered = vbs.filter((v) => v.side === side);
  if (filtered.length === 0) return null;
  return Math.max(...filtered.map((v) => v.edge));
}
