import { useMemo, useState } from "react";
import { AlertTriangle, Ghost, RotateCcw } from "lucide-react";
import { useDashboard } from "@/hooks/use-dashboard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TooltipProvider } from "@/components/ui/tooltip";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import FilterBar, { type FilterState } from "@/components/matches/FilterBar";
import MatchTable, { type SortKey } from "@/components/matches/MatchTable";
import MatchCards from "@/components/matches/MatchCards";

function LoadingState() {
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Skeleton className="h-9 flex-1" />
        <Skeleton className="h-9 w-48" />
      </div>
      <div className="flex gap-1.5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-8 w-20 rounded-full" />
        ))}
      </div>
      <Card className="divide-y">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 px-4 py-3.5">
            <Skeleton className="h-5 w-16" />
            <Skeleton className="h-5 flex-1" />
            <Skeleton className="hidden h-5 w-10 sm:block" />
            <Skeleton className="h-7 w-12" />
            <Skeleton className="h-5 w-14" />
          </div>
        ))}
      </Card>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <Card className="mx-auto mt-10 max-w-md border-destructive/30 p-6 text-center">
      <AlertTriangle className="mx-auto mb-2 !size-8 text-destructive" />
      <h2 className="font-bold">Failed to load dashboard data</h2>
      <p className="mt-1 break-all text-xs text-muted-foreground">{message}</p>
      <p className="mt-1 text-[11px] text-muted-foreground/70">
        Run the Python pipeline to generate data.json.
      </p>
      <Button onClick={onRetry} variant="outline" size="sm" className="mt-4 gap-1.5">
        <RotateCcw className="!size-3.5" /> Retry
      </Button>
    </Card>
  );
}

function EmptyState({ onReset }: { onReset: () => void }) {
  return (
    <Card className="p-10 text-center">
      <Ghost className="mx-auto mb-3 !size-8 text-muted-foreground/50" />
      <h2 className="text-sm font-semibold">No matches match your filters</h2>
      <p className="mt-1 text-xs text-muted-foreground">Try removing a source filter or clearing the search.</p>
      <Button onClick={onReset} variant="outline" size="sm" className="mt-4 gap-1.5">
        <RotateCcw className="!size-3.5" /> Reset filters
      </Button>
    </Card>
  );
}

export default function App() {
  const { data, error, loading, reload } = useDashboard();
  const [filters, setFilters] = useState<FilterState>({
    sources: new Set(),
    league: "all",
    query: "",
  });
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState(1);
  const [selectedId, setSelectedId] = useState<string | number | null>(null);

  const matches = data?.matches ?? [];

  const visible = useMemo(() => {
    const q = filters.query.trim().toLowerCase();
    return matches.filter((m) => {
      if (filters.league !== "all" && m.league !== filters.league) return false;
      if (q && !m.home_team.toLowerCase().includes(q) && !m.away_team.toLowerCase().includes(q))
        return false;
      for (const s of filters.sources) if (!m.sources?.[s]) return false;
      return true;
    });
  }, [matches, filters]);

  const onSort = (k: SortKey) => {
    if (sortKey === k) setSortDir((d) => -d);
    else {
      setSortKey(k);
      setSortDir(1);
    }
  };

  const resetFilters = () =>
    setFilters({ sources: new Set(), league: "all", query: "" });

  return (
    <TooltipProvider delayDuration={200}>
      <div className="min-h-dvh">
        <Header data={data} />

        <main className="container py-4 sm:py-6">
          {loading ? (
            <LoadingState />
          ) : error ? (
            <ErrorState message={error} onRetry={reload} />
          ) : data ? (
            <>
              <FilterBar matches={matches} filters={filters} onChange={setFilters} />

              {visible.length === 0 ? (
                <EmptyState onReset={resetFilters} />
              ) : (
                <>
                  <div className="mt-4 hidden md:block">
                    <MatchTable
                      matches={visible}
                      sortKey={sortKey}
                      sortDir={sortDir}
                      onSort={onSort}
                      selectedId={selectedId}
                      onToggle={(id) => setSelectedId((cur) => (cur === id ? null : id))}
                      rollingWindow={data.rolling_window}
                    />
                  </div>
                  <div className="mt-4 md:hidden">
                    <MatchCards matches={visible} rollingWindow={data.rolling_window} />
                  </div>
                </>
              )}

              <Footer data={data} visibleCount={visible.length} />
            </>
          ) : null}
        </main>
      </div>
    </TooltipProvider>
  );
}
