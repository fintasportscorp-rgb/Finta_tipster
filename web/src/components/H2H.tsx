import type { H2H as H2HType } from "../types";

export default function H2H({
  h2h,
  homeTeam,
  awayTeam,
}: {
  h2h: H2HType | null;
  homeTeam: string;
  awayTeam: string;
}) {
  if (!h2h) return <div className="text-dim text-xs">No H2H data</div>;
  const t = h2h.a_wins + h2h.draws + h2h.b_wins;
  if (t === 0) return <div className="text-dim text-xs">No H2H data</div>;
  const aP = Math.round((h2h.a_wins / t) * 100);
  const dP = Math.round((h2h.draws / t) * 100);
  const bP = 100 - aP - dP;

  return (
    <div>
      <div className="text-[11px] text-dim mb-1">
        {homeTeam} W - D - {awayTeam} W
      </div>
      <div className="flex h-[22px] rounded-[5px] overflow-hidden my-1.5">
        {aP > 0 && (
          <div className="grid place-items-center text-[10px] font-bold text-white bg-good" style={{ width: `${aP}%` }}>
            {h2h.a_wins}
          </div>
        )}
        {dP > 0 && (
          <div className="grid place-items-center text-[10px] font-bold text-black/80 bg-warn" style={{ width: `${dP}%` }}>
            {h2h.draws}
          </div>
        )}
        {bP > 0 && (
          <div className="grid place-items-center text-[10px] font-bold text-white bg-bad" style={{ width: `${bP}%` }}>
            {h2h.b_wins}
          </div>
        )}
      </div>
      <div className="flex gap-1.5 flex-wrap mt-1">
        {h2h.matches.slice(0, 6).map((m, i) => (
          <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-card2 border border-border2">
            <span
              className={`font-semibold ${m.winner === "a" ? "text-good" : m.winner === "b" ? "text-bad" : "text-warn"}`}
            >
              {m.score}
            </span>{" "}
            {m.date}
          </span>
        ))}
      </div>
    </div>
  );
}
