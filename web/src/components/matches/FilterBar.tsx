import { RotateCcw, Search, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { SOURCES } from "@/lib/format";
import type { Match, SourceKey } from "@/types";

export interface FilterState {
  sources: Set<SourceKey>;
  league: string;
  query: string;
}

export default function FilterBar({
  matches,
  filters,
  onChange,
}: {
  matches: Match[];
  filters: FilterState;
  onChange: (next: FilterState) => void;
}) {
  const sourceCounts = new Map<SourceKey, number>();
  for (const s of SOURCES) {
    sourceCounts.set(
      s.key,
      matches.reduce((n, m) => n + (m.sources?.[s.key] ? 1 : 0), 0),
    );
  }
  const leagues = Array.from(new Set(matches.map((m) => m.league))).sort();

  const isFiltered =
    filters.sources.size > 0 || filters.league !== "all" || filters.query.trim() !== "";

  const reset = () => onChange({ sources: new Set(), league: "all", query: "" });

  return (
    <section aria-label="Filters" className="space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={filters.query}
            onChange={(e) => onChange({ ...filters, query: e.target.value })}
            placeholder="Search teams…"
            className="pl-8"
            aria-label="Search teams"
          />
        </div>
        <Select
          value={filters.league}
          onValueChange={(v) => onChange({ ...filters, league: v })}
        >
          <SelectTrigger className="w-full sm:w-56" aria-label="Filter by league">
            <SlidersHorizontal className="mr-1 !size-3.5 opacity-60" />
            <SelectValue placeholder="All leagues" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All leagues</SelectItem>
            {leagues.map((l) => (
              <SelectItem key={l} value={l}>
                {l}{" "}
                <span className="text-muted-foreground">
                  ({matches.filter((m) => m.league === l).length})
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <ToggleGroup
          type="multiple"
          variant="outline"
          size="sm"
          className="flex-wrap justify-start gap-1.5"
          value={Array.from(filters.sources)}
          onValueChange={(vals) =>
            onChange({ ...filters, sources: new Set(vals as SourceKey[]) })
          }
        >
          {SOURCES.map((s) => (
            <ToggleGroupItem key={s.key} value={s.key} aria-label={`Filter by ${s.label}`}>
              {s.label}
              <span className="ml-0.5 rounded-full bg-muted px-1.5 py-px text-[10px] tabular-nums text-muted-foreground data-[state=on]:bg-background/20">
                {sourceCounts.get(s.key)}
              </span>
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
        {isFiltered && (
          <Button variant="ghost" size="sm" onClick={reset} className="gap-1 px-2 text-xs">
            <RotateCcw className="!size-3" /> Reset
          </Button>
        )}
        <span className="hidden text-[11px] text-muted-foreground lg:inline">
          rows must include all active sources
        </span>
      </div>
    </section>
  );
}
