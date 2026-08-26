import type { TeamData } from "@/types";
import { METRICS, metricBarClass } from "@/lib/format";
import { cn } from "@/lib/utils";
import FormBoxes from "@/components/matches/FormBoxes";
import ScoreBadge from "@/components/matches/ScoreBadge";

function BreakdownChips({ t }: { t: TeamData }) {
  const bd = t.form_breakdown;
  const chips: { n: number; label: string; cls: string }[] = [];
  if (bd?.league) chips.push({ n: bd.league, label: "L", cls: "bg-success/15 text-success" });
  if (bd?.friendly) chips.push({ n: bd.friendly, label: "F", cls: "bg-primary/10 text-primary" });
  if (bd?.prev_season)
    chips.push({ n: bd.prev_season, label: "S", cls: "bg-warning/15 text-warning" });
  if (!chips.length) return null;
  return (
    <div className="mt-1 flex items-center justify-center gap-1">
      <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Form</span>
      {chips.map((c, i) => (
        <span
          key={i}
          className={cn("rounded px-1 py-px text-[10px] font-bold tabular-nums", c.cls)}
        >
          {c.n}
          {c.label}
        </span>
      ))}
    </div>
  );
}

export default function TeamSummary({
  t,
  weights,
}: {
  t: TeamData;
  weights: Record<string, number>;
}) {
  return (
    <div className="rounded-lg border bg-muted/20 p-3 sm:p-4">
      <div className="flex items-center justify-between gap-2">
        <h3 className="min-w-0 truncate text-sm font-bold sm:text-base">{t.team}</h3>
        <ScoreBadge score={t.score} size="lg" />
      </div>
      <BreakdownChips t={t} />
      <FormBoxes form={t.form_string} boxClass="h-6 w-6 text-[11px]" className="mt-2.5 justify-center" />

      <div className="mt-3 space-y-2">
        {METRICS.map((m) => {
          const v = t.components?.[m.key];
          if (v == null) return null;
          const w = weights[m.key] != null ? Math.round(weights[m.key] * (weights[m.key] <= 1 ? 100 : 1)) : null;
          return (
            <div key={m.key}>
              <div className="mb-0.5 flex items-baseline justify-between text-[11px]">
                <span className="text-muted-foreground">
                  {m.label}
                  {w != null && <span className="ml-1 opacity-60">{w}%</span>}
                </span>
                <span className="font-semibold tabular-nums">{Math.round(v)}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-border">
                <div
                  className={cn("h-full rounded-full transition-all", metricBarClass(v))}
                  style={{ width: `${Math.max(2, Math.min(100, v))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {t.last_formation && (
        <p className="mt-3 text-center text-xs text-muted-foreground">
          Last XI{" "}
          <strong className="font-semibold text-primary">{t.last_formation}</strong>
        </p>
      )}
    </div>
  );
}
