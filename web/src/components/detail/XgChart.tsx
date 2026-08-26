import type { XgPoint } from "@/types";
import SectionTitle from "./SectionTitle";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export default function XgChart({
  team,
  data,
  window,
}: {
  team: string;
  data?: XgPoint[];
  window: number;
}) {
  if (!data || data.length === 0) {
    return (
      <div>
        <SectionTitle>{team}</SectionTitle>
        <p className="text-xs text-muted-foreground">No xG data</p>
      </div>
    );
  }
  const max = Math.max(...data.map((x) => Math.abs(x.diff)), 0.5);
  const totalDiff = data.reduce((s, x) => s + x.diff, 0);
  return (
    <div>
      <SectionTitle right={`last ${window} · Σ ${totalDiff >= 0 ? "+" : ""}${totalDiff.toFixed(2)} xG`}>
        xG rolling — {team}
      </SectionTitle>
      <div className="flex h-14 items-end gap-[3px] rounded-lg border p-2">
        {data.map((x, i) => (
          <Tooltip key={i}>
            <TooltipTrigger asChild>
              <div
                className="group relative min-h-[3px] flex-1 cursor-default rounded-t-sm transition-opacity hover:opacity-80"
                style={{
                  height: `${(Math.abs(x.diff) / max) * 100}%`,
                  background:
                    x.diff >= 0
                      ? "hsl(var(--score-high))"
                      : "hsl(var(--score-low))",
                }}
              />
            </TooltipTrigger>
            <TooltipContent side="top">
              <p>
                xG {x.xg.toFixed(2)} — xGA {x.xga.toFixed(2)}
              </p>
              <p className={x.diff >= 0 ? "text-success" : "text-destructive"}>
                diff {x.diff >= 0 ? "+" : ""}
                {x.diff.toFixed(2)}
              </p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </div>
  );
}
