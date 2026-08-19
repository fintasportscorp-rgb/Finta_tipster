import type { Match, SourceKey } from "../types";
import { SOURCES } from "../lib/format";

export default function Filters({
  matches,
  active,
  onToggle,
  onClear,
}: {
  matches: Match[];
  active: Set<SourceKey>;
  onToggle: (k: SourceKey) => void;
  onClear: () => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5 items-center mb-4">
      <span className="text-[11px] text-dim uppercase tracking-wider mr-1">Filter by source:</span>
      {SOURCES.map((s) => {
        const count = matches.filter((m) => m.sources?.[s.key]).length;
        const isActive = active.has(s.key);
        return (
          <button
            key={s.key}
            onClick={() => onToggle(s.key)}
            className={`px-3 py-1 rounded-full border text-xs font-semibold transition ${
              isActive
                ? "bg-accent border-accent text-white"
                : "bg-card border-border text-dim hover:border-border2 hover:text-text"
            }`}
          >
            {s.label}
            <span className="text-[10px] opacity-70 ml-1">{count}</span>
          </button>
        );
      })}
      {active.size > 0 && (
        <button
          onClick={onClear}
          className="px-3 py-1 rounded-full border border-bad text-bad text-xs font-semibold"
        >
          Clear
        </button>
      )}
    </div>
  );
}
