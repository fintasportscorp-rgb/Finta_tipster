import type { ValueBet } from "../types";

function tagColor(edge: number): string {
  return edge >= 15
    ? "bg-good/20 text-good border-good/30"
    : edge >= 10
      ? "bg-warn/20 text-warn border-warn/30"
      : "bg-accent/15 text-accent border-accent/25";
}

export default function ValueBets({ vbs }: { vbs: ValueBet[] }) {
  if (!vbs || vbs.length === 0)
    return (
      <div className="text-dim text-xs">
        No value bets detected — form assessment aligns with market odds
      </div>
    );
  return (
    <div className="scroll-x">
      <table className="w-full border-collapse text-[11px]">
        <thead>
          <tr className="text-dim text-left">
            <th className="font-normal">Side</th>
            <th className="font-normal">Team</th>
            <th className="font-normal">Odds</th>
            <th className="font-normal">Form %</th>
            <th className="font-normal">Implied %</th>
            <th className="font-normal">Edge</th>
          </tr>
        </thead>
        <tbody>
          {vbs.map((v, i) => (
            <tr key={i} className="border-b border-border">
              <td className="py-1">
                <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold border ${tagColor(v.edge)}`}>
                  {v.side === "home" ? "Home" : "Away"}
                </span>
              </td>
              <td>{v.team}</td>
              <td className="font-semibold">{v.odds}</td>
              <td>{v.form_prob}%</td>
              <td>{v.implied_prob}%</td>
              <td className="font-bold text-good">+{v.edge}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
