import type { TeamData } from "../types";

const RESULT: Record<string, string> = { W: "text-good", D: "text-warn", L: "text-bad" };
const BADGE: Record<string, string> = { league: "L", friendly: "F", prev_season: "S" };
const BADGE_COLOR: Record<string, string> = {
  league: "text-dim",
  friendly: "text-info",
  prev_season: "text-warn",
};

export default function FormMatches({ t }: { t: TeamData }) {
  if (!t.form_matches || t.form_matches.length === 0) {
    return <div className="text-dim text-xs">No form matches</div>;
  }
  return (
    <div className="scroll-x">
      <table className="w-full border-collapse text-[11px]">
        <thead>
          <tr className="text-dim text-[10px] text-left">
            <th className="font-normal">Date</th>
            <th className="font-normal">H/A</th>
            <th className="font-normal">Opp</th>
            <th className="font-normal text-center">Sc</th>
            <th className="font-normal text-center">R</th>
            <th className="font-normal text-center">T</th>
          </tr>
        </thead>
        <tbody>
          {t.form_matches.map((m, i) => (
            <tr key={i}>
              <td className="text-dim whitespace-nowrap">{m.date}</td>
              <td>{m.home_away}</td>
              <td className="whitespace-nowrap">{m.opponent}</td>
              <td className="text-center">
                {m.gf}-{m.ga}
              </td>
              <td className={`text-center font-bold ${RESULT[m.result] ?? "text-dim"}`}>
                {m.result}
              </td>
              <td className={`text-center text-[10px] ${BADGE_COLOR[m.type] ?? "text-dim"}`}>
                {BADGE[m.type] ?? "L"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
