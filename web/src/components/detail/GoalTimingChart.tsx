import type { GoalTiming } from "@/types";
import SectionTitle from "./SectionTitle";

export default function GoalTimingChart({
  gt,
  homeTeam,
  awayTeam,
}: {
  gt: GoalTiming | null;
  homeTeam: string;
  awayTeam: string;
}) {
  if (!gt || !gt.segments?.length) return null;
  const max = Math.max(
    ...gt.segments.flatMap((_, i) => [
      gt.home.gf[i] ?? 0,
      gt.home.ga[i] ?? 0,
      gt.away.gf[i] ?? 0,
      gt.away.ga[i] ?? 0,
    ]),
    1,
  );

  const SideRow = ({
    label,
    gf,
    ga,
    color,
  }: {
    label: string;
    gf: number[];
    ga: number[];
    color: string;
  }) => (
    <div className="flex items-center gap-3">
      <span className="w-20 shrink-0 truncate text-[11px] font-medium sm:w-28">{label}</span>
      <div className="flex flex-1 items-end gap-1.5">
        {gf.map((v, i) => (
          <div
            key={i}
            className="flex h-14 flex-1 items-end justify-center gap-0.5"
            title={`Scored ${v} · Conceded ${ga[i] ?? 0}`}
          >
            <div
              className="w-full max-w-3 rounded-t-sm"
              style={{ height: `${Math.max(4, ((v ?? 0) / max) * 56)}px`, background: color }}
            />
            <div
              className="w-full max-w-3 rounded-t-sm opacity-40"
              style={{ height: `${Math.max(4, ((ga[i] ?? 0) / max) * 56)}px`, background: color }}
            />
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div>
      <SectionTitle
        right={
          <span className="flex items-center gap-1">
            <i className="inline-block h-2 w-2 rounded-sm bg-primary" /> scored
            <i className="ml-1.5 inline-block h-2 w-2 rounded-sm bg-primary/40" /> conceded
          </span>
        }
      >
        Goal timing by 15-min segment
      </SectionTitle>
      <div className="space-y-2 rounded-lg border p-3">
        <SideRow label={homeTeam} gf={gt.home.gf} ga={gt.home.ga} color="hsl(var(--primary))" />
        <SideRow label={awayTeam} gf={gt.away.gf} ga={gt.away.ga} color="hsl(var(--success))" />
        <div className="flex gap-1.5 pl-[calc(5rem+0.75rem)] sm:pl-[calc(7rem+0.75rem)]">
          {gt.segments.map((s, i) => (
            <div key={i} className="flex-1 text-center text-[9px] tabular-nums text-muted-foreground">
              {s}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
