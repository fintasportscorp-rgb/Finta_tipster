import type { H2H } from "@/types";
import SectionTitle from "./SectionTitle";
import { cn } from "@/lib/utils";

export default function H2HPanel({
  h2h,
  homeTeam,
  awayTeam,
}: {
  h2h: H2H | null;
  homeTeam: string;
  awayTeam: string;
}) {
  if (!h2h) {
    return (
      <div>
        <SectionTitle>Head to head</SectionTitle>
        <p className="text-xs text-muted-foreground">No H2H data</p>
      </div>
    );
  }
  const total = h2h.a_wins + h2h.draws + h2h.b_wins;
  if (total === 0) {
    return (
      <div>
        <SectionTitle>Head to head</SectionTitle>
        <p className="text-xs text-muted-foreground">No H2H data</p>
      </div>
    );
  }
  const aP = Math.round((h2h.a_wins / total) * 100);
  const dP = Math.round((h2h.draws / total) * 100);
  const bP = 100 - aP - dP;

  return (
    <div>
      <SectionTitle right={`${total} meetings`}>Head to head</SectionTitle>
      <div className="mb-1 flex justify-between text-[11px] text-muted-foreground">
        <span>
          <span className="font-semibold text-success">{homeTeam}</span> wins
        </span>
        <span>{h2h.a_wins}–{h2h.draws}–{h2h.b_wins}</span>
        <span>
          <span className="font-semibold text-destructive">{awayTeam}</span> wins
        </span>
      </div>
      <div className="flex h-6 overflow-hidden rounded-md">
        {aP > 0 && (
          <div
            className="grid place-items-center bg-[color:hsl(var(--score-high))] text-[10px] font-bold text-white"
            style={{ width: `${aP}%` }}
          >
            {aP >= 12 && h2h.a_wins}
          </div>
        )}
        {dP > 0 && (
          <div
            className="grid place-items-center bg-warning text-[10px] font-bold text-black/80"
            style={{ width: `${dP}%` }}
          >
            {dP >= 12 && h2h.draws}
          </div>
        )}
        {bP > 0 && (
          <div
            className="grid place-items-center bg-destructive text-[10px] font-bold text-white"
            style={{ width: `${bP}%` }}
          >
            {bP >= 12 && h2h.b_wins}
          </div>
        )}
      </div>
      <div className="mt-1.5 flex flex-wrap gap-1">
        {h2h.matches.slice(0, 8).map((m, i) => (
          <span
            key={i}
            className="rounded-md border bg-muted/40 px-1.5 py-0.5 text-[10px] tabular-nums"
          >
            <span
              className={cn(
                "font-bold",
                m.winner === "a" ? "text-success" : m.winner === "b" ? "text-destructive" : "text-warning",
              )}
            >
              {m.score}
            </span>{" "}
            <span className="text-muted-foreground">{m.date}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
