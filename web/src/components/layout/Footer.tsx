import { METRICS } from "@/lib/format";
import type { Dashboard } from "@/types";

export default function Footer({
  data,
  visibleCount,
}: {
  data: Dashboard;
  visibleCount: number;
}) {
  const weights = data.weights ?? {};
  return (
    <footer className="mt-6 space-y-1 pb-8 text-center text-[11px] leading-relaxed text-muted-foreground">
      <p>
        Form score weights:{" "}
        {METRICS.map((m, i) => (
          <span key={m.key}>
            {i > 0 && " · "}
            {m.label} {weights[m.key] != null ? `${Math.round(weights[m.key] * (String(weights[m.key]).includes(".") ? 100 : 1))}%` : ""}
          </span>
        ))}
      </p>
      <p className="opacity-70">
        Form: L = league · F = friendly · S = last season (friendlies used when &lt;{" "}
        {data.league_match_threshold} league matches) · Rolling xG window: {data.rolling_window}{" "}
        matches
      </p>
      <p className="opacity-70">
        Showing {visibleCount} of {data.matches.length} matches — tap any row for the full breakdown
      </p>
    </footer>
  );
}
