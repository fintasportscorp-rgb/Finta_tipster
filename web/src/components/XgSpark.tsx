import type { XgPoint } from "../types";

export default function XgSpark({ data }: { data: XgPoint[] }) {
  if (!data || data.length === 0) return <div className="text-dim text-xs">No xG data</div>;
  const mx = Math.max(...data.map((x) => Math.abs(x.diff)), 0.5);
  return (
    <div className="flex items-end gap-[2px] h-9">
      {data.map((x, i) => (
        <div
          key={i}
          title={`xG:${x.xg} xGA:${x.xga}`}
          className={`flex-1 rounded-t-[2px] min-h-[2px] ${x.diff >= 0 ? "bg-good" : "bg-bad"}`}
          style={{ height: `${(Math.abs(x.diff) / mx) * 100}%` }}
        />
      ))}
    </div>
  );
}
