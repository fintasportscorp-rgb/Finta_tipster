import { useMemo } from "react";
import type { Match } from "@/types";
import { buildMarkets, matchPrediction } from "@/lib/prediction";
import SectionTitle from "./SectionTitle";
import { cn } from "@/lib/utils";

export default function OddsMarkets({ m }: { m: Match }) {
  const pred = useMemo(() => matchPrediction(m), [m]);
  const markets = useMemo(() => buildMarkets(m, pred), [m, pred]);

  if (!markets.length) {
    return (
      <div>
        <SectionTitle>Match odds</SectionTitle>
        <p className="text-xs text-muted-foreground">No odds data</p>
      </div>
    );
  }

  return (
    <div>
      <SectionTitle right="highlight = model pick">Match odds</SectionTitle>
      <div className="space-y-2">
        {markets.map((mk, mi) => (
          <div key={mi} className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="w-full shrink-0 text-[11px] font-medium text-muted-foreground sm:w-32">
              {mk.name}
            </span>
            <div className="flex flex-wrap gap-1">
              {mk.choices.map(([choice, odds], i) => {
                const isPick = i === mk.predicted;
                return (
                  <span
                    key={i}
                    title={isPick ? "Predicted pick from recent form" : undefined}
                    className={cn(
                      "rounded-md border px-1.5 py-0.5 text-[11px] tabular-nums",
                      isPick
                        ? "border-success/40 bg-success/10 font-bold text-success"
                        : "border-border bg-muted/30 text-muted-foreground",
                    )}
                  >
                    {choice}{" "}
                    <span className={isPick ? "" : "font-semibold"}>{(+odds).toFixed(2)}</span>
                  </span>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      {pred.total != null && pred.eh != null && pred.ea != null && (
        <p className="mt-2 text-[10px] leading-relaxed text-muted-foreground/80">
          Model (recent form): exp. goals {m.home_team} {pred.eh.toFixed(1)} — {m.away_team}{" "}
          {pred.ea.toFixed(1)} · total {pred.total.toFixed(1)}
        </p>
      )}
    </div>
  );
}
