import { useEffect, useMemo, useState } from "react";
import type { Dashboard, Match, SourceKey } from "./types";
import Filters from "./components/Filters";
import MatchTable, { type SortKey } from "./components/MatchTable";

export default function App() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<Set<SourceKey>>(new Set());
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState(1);
  const [selectedId, setSelectedId] = useState<string | number | null>(null);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: Dashboard) => setData(d))
      .catch((e) => setError(String(e)));
  }, []);

  const matches = data?.matches ?? [];

  const passesFilters = (m: Match, filters: Set<SourceKey>) => {
    if (filters.size === 0) return true;
    for (const f of filters) if (!m.sources?.[f]) return false;
    return true;
  };

  const visible = useMemo(
    () => matches.filter((m) => passesFilters(m, active)),
    [matches, active],
  );

  const toggleFilter = (k: SourceKey) => {
    const next = new Set(active);
    next.has(k) ? next.delete(k) : next.add(k);
    setActive(next);
    // Collapse the open row if it no longer passes the new filter set.
    const sel = matches.find((x) => x.id === selectedId);
    if (sel && !passesFilters(sel, next)) setSelectedId(null);
  };

  const onSort = (k: SortKey) => {
    if (sortKey === k) setSortDir((d) => -d);
    else {
      setSortKey(k);
      setSortDir(1);
    }
  };

  const onToggleMatch = (id: string | number) =>
    setSelectedId((cur) => (cur === id ? null : id));

  if (error)
    return (
      <div className="p-8 text-center text-bad">
        Failed to load data.json — {error}
        <div className="text-dim text-sm mt-2">Run the Python build to generate it.</div>
      </div>
    );
  if (!data)
    return <div className="p-8 text-center text-dim">Loading…</div>;

  return (
    <div className="p-2 sm:p-4">
      <div className="max-w-[1100px] mx-auto w-full">
        <header className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 mb-4">
          <h1 className="text-lg sm:text-xl font-bold">Finta Tipster — Big 5 Match Form</h1>
          <div className="text-xs text-dim">
            {matches.length} matches · {data.generated_at}
          </div>
        </header>

        <Filters
          matches={matches}
          active={active}
          onToggle={toggleFilter}
          onClear={() => setActive(new Set())}
        />

        {visible.length === 0 ? (
          <div className="text-center text-dim py-10 text-base">No matches match the filters.</div>
        ) : (
          <MatchTable
            matches={visible}
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={onSort}
            selectedId={selectedId}
            onToggle={onToggleMatch}
            rollingWindow={data.rolling_window}
          />
        )}

        <div className="text-center text-dim mt-2 text-xs">
          {visible.length} / {matches.length} matches
        </div>

        <footer className="text-center mt-5 text-dim text-[11px] leading-relaxed">
          Weights: Results 25% · xG 20% · Availability 20% · Formation 10% · Market 15% · Tipsters
          10% · Form: L=League F=Friendly S=Last Season (friendlies used when &lt;
          {data.league_match_threshold} league matches) · Tap a row to expand
        </footer>
      </div>
    </div>
  );
}
