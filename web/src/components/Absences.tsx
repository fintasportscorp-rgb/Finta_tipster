import type { Absence } from "../types";

const BADGE_COLOR: Record<string, string> = {
  Injured: "bg-bad/15 text-bad",
  Suspended: "bg-[#ff8c00]/15 text-[#ff8c00]",
  Loaned: "bg-info/15 text-info",
  Not: "bg-accent/15 text-accent",
  International: "bg-good/15 text-good",
};

export default function Absences({ absences }: { absences: Absence[] }) {
  if (!absences || absences.length === 0)
    return <div className="text-dim text-xs">No absences</div>;
  return (
    <div>
      {absences.map((a, i) => {
        const bt = (a.type || a.status || "").split("(")[0].trim() || "Unknown";
        const bc = bt.split(" ")[0];
        return (
          <div
            key={i}
            className="flex justify-between items-center py-1 border-b border-border last:border-0 text-xs"
          >
            <div>
              <span className="font-semibold">{a.player}</span>
              <span className="text-dim text-[10px] ml-1">{a.position}</span>
            </div>
            <span className={`text-[9px] px-1.5 py-0.5 rounded font-semibold ${BADGE_COLOR[bc] ?? "bg-border text-dim"}`}>
              {bt}
            </span>
          </div>
        );
      })}
    </div>
  );
}
