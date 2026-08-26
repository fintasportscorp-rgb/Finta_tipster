import type { Match, SourceKey } from "@/types";

export const METRICS = [
  { key: "results", label: "Results" },
  { key: "xg", label: "xG" },
  { key: "availability", label: "Availability" },
  { key: "formation", label: "Formation" },
  { key: "odds", label: "Odds" },
  { key: "tips", label: "Tips" },
] as const;

export type MetricKey = (typeof METRICS)[number]["key"];

export const SOURCES: { key: SourceKey; label: string }[] = [
  { key: "results", label: "Results" },
  { key: "xg", label: "xG" },
  { key: "availability", label: "Absences" },
  { key: "formation", label: "Formation" },
  { key: "odds", label: "Odds" },
  { key: "tips", label: "Tipsters" },
  { key: "h2h", label: "H2H" },
];

const LEAGUE_COLORS: Record<string, string> = {
  "Serie A": "#3f8cff",
  "Premier League": "#e63c2f",
  "La Liga": "#f28a00",
  Bundesliga: "#d40b0b",
  "Ligue 1": "#ad0dd6",
};

export function leagueColor(league: string): string {
  return LEAGUE_COLORS[league] ?? "hsl(var(--muted-foreground))";
}

export type ScoreBand = "high" | "mid" | "low";

export function scoreBand(s: number): ScoreBand {
  return s >= 70 ? "high" : s >= 50 ? "mid" : "low";
}

const BAND_TEXT: Record<ScoreBand, string> = {
  high: "text-[color:hsl(var(--score-high))]",
  mid: "text-[color:hsl(var(--score-mid))]",
  low: "text-[color:hsl(var(--score-low))]",
};

const BAND_BG_SOFT: Record<ScoreBand, string> = {
  high: "bg-[color:hsl(var(--score-high)/0.12)] text-[color:hsl(var(--score-high))]",
  mid: "bg-[color:hsl(var(--score-mid)/0.14)] text-[color:hsl(var(--score-mid))]",
  low: "bg-[color:hsl(var(--score-low)/0.12)] text-[color:hsl(var(--score-low))]",
};

const BAND_BAR: Record<ScoreBand, string> = {
  high: "bg-[color:hsl(var(--score-high))]",
  mid: "bg-[color:hsl(var(--score-mid))]",
  low: "bg-[color:hsl(var(--score-low))]",
};

export function scoreTextClass(s: number): string {
  return BAND_TEXT[scoreBand(s)];
}
export function scoreChipClass(s: number): string {
  return BAND_BG_SOFT[scoreBand(s)];
}
export function metricBarClass(v: number): string {
  return BAND_BAR[v >= 60 ? "high" : v >= 40 ? "mid" : "low"];
}

export function validityClass(validity: number, total: number): string {
  return BAND_TEXT[validity >= total * 0.7 ? "high" : validity >= total * 0.4 ? "mid" : "low"];
}

export function absencesChipClass(n: number): string {
  if (n === 0) return "bg-muted text-muted-foreground";
  if (n <= 3) return BAND_BG_SOFT.mid;
  return BAND_BG_SOFT.low;
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

export function edgeTier(edge: number): "strong" | "good" | "lean" {
  return edge >= 15 ? "strong" : edge >= 10 ? "good" : "lean";
}

export const EDGE_TIER_CLASS: Record<"strong" | "good" | "lean", string> = {
  strong:
    "bg-[color:hsl(var(--score-high)/0.15)] text-[color:hsl(var(--score-high))] ring-1 ring-inset ring-[color:hsl(var(--score-high)/0.35)]",
  good: "bg-warning/15 text-warning ring-1 ring-inset ring-warning/30",
  lean: "bg-primary/10 text-primary ring-1 ring-inset ring-primary/25",
};
