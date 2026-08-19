import type { Tip } from "../types";

const FAVOR_COLOR: Record<string, string> = {
  home: "bg-good/15 text-good",
  away: "bg-bad/15 text-bad",
  neutral: "bg-warn/15 text-warn",
  draw: "bg-warn/15 text-warn",
};

export default function Tips({ tips }: { tips: Tip[] }) {
  if (!tips || tips.length === 0)
    return <div className="text-dim text-xs">No tipster data</div>;
  return (
    <div>
      {tips.slice(0, 8).map((t, i) => (
        <div
          key={i}
          className="flex items-center gap-2.5 py-1 border-b border-border last:border-0 text-xs"
        >
          <span className="text-accent font-semibold min-w-[80px] text-[11px]">{t.website}</span>
          <span className="flex-1">{t.tip}</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${FAVOR_COLOR[t.favor] ?? "bg-card2 text-dim"}`}>
            {t.favor}
          </span>
        </div>
      ))}
    </div>
  );
}
