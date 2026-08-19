import type { FormationHist } from "../types";

export default function Formations({ hist }: { hist: FormationHist[] }) {
  if (!hist || hist.length === 0) return <div className="text-dim text-xs">No data</div>;
  return (
    <div className="flex gap-1 flex-wrap">
      {hist.slice(0, 8).map((f, i) => (
        <span
          key={i}
          className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-card2 border border-border2"
        >
          {f.formation}
          <span className="text-dim text-[8px] ml-0.5">MW{f.matchday}</span>
        </span>
      ))}
    </div>
  );
}
