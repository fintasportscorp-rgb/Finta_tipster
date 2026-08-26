export interface FormMatch {
  date: string;
  opponent: string;
  home_away: "H" | "A";
  gf: number;
  ga: number;
  xg: number | null;
  xga: number | null;
  result: "W" | "D" | "L";
  type: "league" | "friendly" | "prev_season" | string;
}

export interface XgPoint {
  xg: number;
  xga: number;
  diff: number;
}

export interface Absence {
  player: string;
  position: string;
  type?: string;
  status?: string;
}

export interface FormationHist {
  formation: string;
  matchday: number;
}

export interface TeamComponents {
  results: number | null;
  xg: number | null;
  availability: number | null;
  odds: number | null;
  tips: number | null;
  timing: number | null;
}

export interface TeamData {
  team: string;
  score: number;
  components: TeamComponents;
  form_string: string[];
  xg_rolling: XgPoint[];
  absences: Absence[];
  absent_count: number;
  last_formation: string | null;
  formation_history: FormationHist[];
  radical_changes: number;
  form_breakdown: { league: number; friendly: number; prev_season: number };
  form_matches: FormMatch[];
}

export interface OddsChoice {
  choice: string;
  odds: number;
}

export interface Odds {
  home: number | null;
  draw: number | null;
  away: number | null;
  other_markets: Record<string, OddsChoice[]> | null;
}

export interface ValueBet {
  side: "home" | "away";
  team: string;
  odds: number;
  form_prob: number;
  implied_prob: number;
  edge: number;
}

export interface H2HMatch {
  score: string;
  date: string;
  winner: "a" | "b" | "draw" | string;
}

export interface H2H {
  a_wins: number;
  draws: number;
  b_wins: number;
  matches: H2HMatch[];
}

export interface Tip {
  website: string;
  tip: string;
  favor: "home" | "away" | "draw" | "neutral" | string;
}

export type SourceKey =
  | "results"
  | "xg"
  | "availability"
  | "odds"
  | "tips"
  | "timing";

export interface GoalTimingSide {
  gf: number[];
  ga: number[];
}

export interface GoalTiming {
  segments: string[];
  home: GoalTimingSide;
  away: GoalTimingSide;
}

export interface Match {
  id: string | number;
  league: string;
  datetime: string;
  date_short: string;
  gameweek: number | null;
  home_team: string;
  away_team: string;
  home: TeamData;
  away: TeamData;
  odds: Odds;
  tips: Tip[];
  tips_summary: { home: number; away: number } | null;
  h2h: H2H | null;
  sources: Record<SourceKey, boolean>;
  validity: number;
  validity_total: number;
  value_bets: ValueBet[];
  goal_timing: GoalTiming | null;
}

export interface Dashboard {
  matches: Match[];
  weights: Record<string, number>;
  rolling_window: number;
  league_match_threshold: number;
  generated_at: string;
}
