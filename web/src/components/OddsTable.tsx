import type { Match } from "../types";
import { matchPrediction, buildMarkets } from "../lib/prediction";

export default function OddsTable({ m }: { m: Match }) {
  if (!m.odds) return <div className="text-dim text-xs">No odds data</div>;
  const pred = matchPrediction(m);
  const markets = buildMarkets(m, pred);
  if (!markets.length) return <div className="text-dim text-xs">No odds data</div>;

  return (
    <div>
      <table className="w-full border-collapse text-[11px] mt-1.5">
        <tbody>
          {markets.map((mk, mi) => (
            <tr key={mi} className="border-b border-border">
              <td className="text-dim whitespace-nowrap pr-2 py-1.5 align-top">{mk.name}</td>
              <td className="py-1.5">
                <div className="flex flex-wrap gap-1 justify-end max-[480px]:justify-start">
                  {mk.choices.map((c, i) => {
                    const odds = (+c[1]).toFixed(2);
                    const isPred = i === mk.predicted;
                    return (
                      <span
                        key={i}
                        title={isPred ? "Model pick from recent form" : undefined}
                        className={`inline-block px-1.5 py-0.5 rounded-[5px] border font-semibold whitespace-nowrap ${
                          isPred
                            ? "bg-good/15 border-good/45 text-good"
                            : "bg-card border-border text-dim"
                        }`}
                      >
                        {c[0]}{" "}
                        {isPred ? <b className="text-good font-extrabold">{odds}</b> : odds}
                      </span>
                    );
                  })}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {pred.total != null && (
        <div className="text-[9px] text-dimmer mt-1.5 text-center leading-relaxed">
          Model from recent form — exp. goals {m.home_team} {pred.eh!.toFixed(1)} · {m.away_team}{" "}
          {pred.ea!.toFixed(1)} (total {pred.total.toFixed(1)}). Highlighted = predicted pick.
        </div>
      )}
    </div>
  );
}
