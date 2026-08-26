import type { ValueBet } from "@/types";
import { EDGE_TIER_CLASS, edgeTier } from "@/lib/format";
import SectionTitle from "./SectionTitle";

export default function ValueBetsPanel({ vbs }: { vbs?: ValueBet[] }) {
  return (
    <div>
      <SectionTitle>Value bets</SectionTitle>
      {!vbs || vbs.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          None detected — form assessment aligns with the market.
        </p>
      ) : (
        <div className="overflow-x-auto scrollbar-thin rounded-lg border">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr className="border-b bg-muted/40 text-left text-[10px] uppercase tracking-wide text-muted-foreground">
                <th className="px-2 py-1.5 font-semibold">Side</th>
                <th className="px-2 py-1.5 font-semibold">Team</th>
                <th className="px-2 py-1.5 text-right font-semibold">Odds</th>
                <th className="px-2 py-1.5 text-right font-semibold">Form %</th>
                <th className="px-2 py-1.5 text-right font-semibold">Implied %</th>
                <th className="px-2 py-1.5 text-right font-semibold">Edge</th>
              </tr>
            </thead>
            <tbody>
              {vbs.map((v, i) => (
                <tr key={i} className="border-b border-border/50 last:border-0">
                  <td className="px-2 py-1.5 capitalize text-muted-foreground">{v.side}</td>
                  <td className="max-w-[10rem] truncate px-2 py-1.5 font-medium">{v.team}</td>
                  <td className="px-2 py-1.5 text-right font-semibold tabular-nums">{v.odds}</td>
                  <td className="px-2 py-1.5 text-right tabular-nums">{v.form_prob}%</td>
                  <td className="px-2 py-1.5 text-right tabular-nums text-muted-foreground">
                    {v.implied_prob}%
                  </td>
                  <td className="px-2 py-1.5 text-right">
                    <span
                      className={`inline-block rounded-md px-1.5 py-0.5 text-[11px] font-extrabold tabular-nums ${
                        EDGE_TIER_CLASS[edgeTier(v.edge)]
                      }`}
                    >
                      +{v.edge}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
