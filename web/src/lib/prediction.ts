import type { Match, FormMatch, OddsChoice } from "@/types";

function avgGoals(fm: FormMatch[] | undefined) {
  if (!fm || !fm.length) return null;
  let gf = 0,
    ga = 0,
    n = 0;
  for (const x of fm) {
    gf += x.gf || 0;
    ga += x.ga || 0;
    n++;
  }
  return n ? { gf: gf / n, ga: ga / n } : null;
}

export interface Prediction {
  eh: number | null;
  ea: number | null;
  total: number | null;
  result: "H" | "D" | "A";
}

export function matchPrediction(m: Match): Prediction {
  const hg = avgGoals(m.home.form_matches);
  const ag = avgGoals(m.away.form_matches);
  let eh: number | null = null,
    ea: number | null = null,
    total: number | null = null;
  if (hg && ag) {
    eh = (hg.gf + ag.ga) / 2;
    ea = (ag.gf + hg.ga) / 2;
    total = eh + ea;
  }
  const diff = (m.home.score || 0) - (m.away.score || 0);
  const result = diff > 5 ? "H" : diff < -5 ? "A" : "D";
  return { eh, ea, total, result };
}

function parseLine(s: string): number | null {
  const mch = String(s).match(/(\d+(?:\.\d+)?)/);
  return mch ? parseFloat(mch[1]) : null;
}

export function predictedIndex(
  name: string,
  choices: [string, number][],
  pred: Prediction,
  m: Match,
): number {
  const mn = (name || "").toLowerCase();
  const norm = choices.map((c) => String(c[0]).toLowerCase().trim());

  const isOU =
    norm.some((c) => /(^|\s)(over|under|o|u)(\s|$|\d|\/)/.test(c)) ||
    /over|under|o\/u/.test(mn);
  if (isOU && pred.total != null) {
    let ref = pred.total;
    if (/home/.test(mn) && pred.eh != null) ref = pred.eh;
    else if (/away/.test(mn) && pred.ea != null) ref = pred.ea;
    let line: number | null = null;
    norm.forEach((c) => {
      const l = parseLine(c);
      if (l != null) line = l;
    });
    if (line == null) line = parseLine(mn);
    if (line == null) line = 2.5;
    const wantOver = ref > line;
    for (let i = 0; i < norm.length; i++) {
      if (wantOver && /over|^o/.test(norm[i])) return i;
      if (!wantOver && /under|^u/.test(norm[i])) return i;
    }
  }

  if (
    /both teams|btts|gg\/ng/.test(mn) ||
    (norm.includes("yes") && norm.includes("no"))
  ) {
    if (pred.eh != null && pred.ea != null) {
      const yes = pred.eh >= 0.8 && pred.ea >= 0.8;
      for (let i = 0; i < norm.length; i++) {
        if (yes && /yes|gg/.test(norm[i])) return i;
        if (!yes && /no|ng/.test(norm[i])) return i;
      }
    }
  }

  if (
    /double chance/.test(mn) ||
    norm.some((c) => /^(1x|12|x2)$/.test(c.replace(/\s/g, "")))
  ) {
    for (let i = 0; i < norm.length; i++) {
      const c = norm[i].replace(/\s/g, "");
      if (pred.result === "H" && /(1x|12)/.test(c)) return i;
      if (pred.result === "A" && /(x2|12)/.test(c)) return i;
      if (pred.result === "D" && /(1x|x2)/.test(c)) return i;
    }
  }

  const home = (m.home_team || "").toLowerCase();
  const away = (m.away_team || "").toLowerCase();
  const cat = (c: string): "H" | "A" | "D" | null => {
    if (c === "1" || c === "home" || (home && c === home)) return "H";
    if (c === "2" || c === "away" || (away && c === away)) return "A";
    if (c === "x" || c === "draw" || c === "tie") return "D";
    return null;
  };
  if (norm.some((c) => cat(c) !== null)) {
    for (let i = 0; i < norm.length; i++) if (cat(norm[i]) === pred.result) return i;
  }
  return -1;
}

export interface OddsMarket {
  name: string;
  choices: [string, number][];
  predicted: number;
}

export function buildMarkets(m: Match, pred: Prediction): OddsMarket[] {
  const markets: OddsMarket[] = [];
  if (m.odds?.home) {
    const ch: [string, number][] = (
      [
        ["Home", m.odds.home],
        ["Draw", m.odds.draw],
        ["Away", m.odds.away],
      ] as [string, number | null][]
    ).filter((c) => c[1] != null) as [string, number][];
    if (ch.length >= 2)
      markets.push({
        name: "Match Result",
        choices: ch,
        predicted: predictedIndex("Match Result", ch, pred, m),
      });
  }
  const other = m.odds?.other_markets;
  if (other) {
    for (const [mk, list] of Object.entries(other)) {
      if (!list || list.length < 2 || list.length > 6) continue;
      const ch = list
        .filter((c: OddsChoice) => c.odds > 0)
        .map((c: OddsChoice) => [String(c.choice), c.odds] as [string, number]);
      if (ch.length >= 2)
        markets.push({ name: mk, choices: ch, predicted: predictedIndex(mk, ch, pred, m) });
    }
  }
  return markets;
}
