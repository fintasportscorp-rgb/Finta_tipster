import type { TeamComponents } from "../types";
import { METRICS, fillColor } from "../lib/format";

export default function MetricBars({ c }: { c: TeamComponents }) {
  return (
    <div className="mt-2">
      {METRICS.map((m) => {
        const v = c[m.key];
        if (v === null || v === undefined) return null;
        return (
          <div key={m.key} className="my-2">
            <div className="flex justify-between text-[11px] text-dim mb-0.5">
              <span>
                {m.label} <span className="opacity-50">({m.w})</span>
              </span>
              <span>{Math.round(v)}</span>
            </div>
            <div className="h-[5px] bg-border rounded overflow-hidden">
              <div className={`h-full rounded ${fillColor(v)}`} style={{ width: `${v}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
