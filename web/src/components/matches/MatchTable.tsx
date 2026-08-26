import { Fragment, useMemo } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";
import type { Match } from "@/types";
import {
  absencesChipClass,
  formScore,
  getValueEdge,
  scoreTextClass,
} from "@/lib/format";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import FormBoxes from "./FormBoxes";
import LeagueBadge from "./LeagueBadge";
import SourceDots from "./SourceDots";
import ValueEdgeBadge from "./ValueEdgeBadge";
import MatchDetail from "@/components/detail/MatchDetail";

export type SortKey =
  | "league"
  | "datetime"
  | "home_team"
  | "home_score"
  | "home_form"
  | "home_abs"
  | "away_score"
  | "away_form"
  | "away_abs"
  | "away_team"
  | "odds"
  | "validity"
  | "value_home"
  | "value_away";

function sortValue(m: Match, key: SortKey): string | number | null {
  switch (key) {
    case "league":
      return m.league;
    case "datetime":
      return m.datetime;
    case "home_team":
      return m.home.team;
    case "home_score":
      return m.home.score;
    case "home_form":
      return formScore(m.home.form_string);
    case "home_abs":
      return m.home.absent_count;
    case "away_score":
      return m.away.score;
    case "away_form":
      return formScore(m.away.form_string);
    case "away_abs":
      return m.away.absent_count;
    case "away_team":
      return m.away.team;
    case "odds":
      return m.odds?.home || null;
    case "validity":
      return m.validity;
    case "value_home":
      return getValueEdge(m, "home");
    case "value_away":
      return getValueEdge(m, "away");
    default:
      return 0;
  }
}

const LATERAL = "hidden lg:table-cell";

function SortableTh({
  k,
  sortKey,
  sortDir,
  onSort,
  className,
  children,
}: {
  k: SortKey;
  sortKey: SortKey | null;
  sortDir: number;
  onSort: (k: SortKey) => void;
  className?: string;
  children: React.ReactNode;
}) {
  const active = sortKey === k;
  return (
    <TableHead
      aria-sort={active ? (sortDir > 0 ? "ascending" : "descending") : "none"}
      className={cn(className, active && "text-foreground")}
    >
      <button
        onClick={() => onSort(k)}
        className="inline-flex items-center gap-0.5 uppercase tracking-wider hover:text-foreground"
      >
        {children}
        {active ? (
          sortDir > 0 ? (
            <ArrowUp className="!size-3 text-primary" />
          ) : (
            <ArrowDown className="!size-3 text-primary" />
          )
        ) : null}
      </button>
    </TableHead>
  );
}

function OddsCell({ m }: { m: Match }) {
  const o = m.odds;
  if (!o?.home) return <span className="text-muted-foreground/60">—</span>;
  return (
    <span className="whitespace-nowrap text-xs tabular-nums">
      <span className="font-semibold text-primary">{o.home}</span>
      <span className="mx-1 text-muted-foreground/50">·</span>
      <span className="text-muted-foreground">{o.draw ?? "–"}</span>
      <span className="mx-1 text-muted-foreground/50">·</span>
      <span className="font-semibold text-primary">{o.away}</span>
    </span>
  );
}

export default function MatchTable({
  matches,
  sortKey,
  sortDir,
  onSort,
  selectedId,
  onToggle,
  rollingWindow,
}: {
  matches: Match[];
  sortKey: SortKey | null;
  sortDir: number;
  onSort: (k: SortKey) => void;
  selectedId: string | number | null;
  onToggle: (id: string | number) => void;
  rollingWindow: number;
}) {
  const sorted = useMemo(() => {
    const arr = [...matches];
    if (!sortKey) return arr;
    arr.sort((a, b) => {
      const va = sortValue(a, sortKey);
      const vb = sortValue(b, sortKey);
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === "string" && typeof vb === "string")
        return va.localeCompare(vb) * sortDir;
      return (((va as number) || 0) - ((vb as number) || 0)) * sortDir;
    });
    return arr;
  }, [matches, sortKey, sortDir]);

  const COLS = 14;

  return (
    <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
      <Table className="text-[13px]">
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <SortableTh k="league" {...{ sortKey, sortDir, onSort }} className="sticky top-14 z-10">
              Comp
            </SortableTh>
            <SortableTh
              k="datetime"
              {...{ sortKey, sortDir, onSort }}
              className={cn("sticky top-14 z-10", LATERAL)}
            >
              Kick-off
            </SortableTh>
            <SortableTh k="home_team" {...{ sortKey, sortDir, onSort }} className="sticky top-14 z-10">
              Home
            </SortableTh>
            <SortableTh
              k="home_score"
              {...{ sortKey, sortDir, onSort }}
              className="sticky top-14 z-10 text-center"
            >
              Fm
            </SortableTh>
            <SortableTh
              k="home_form"
              {...{ sortKey, sortDir, onSort }}
              className={cn("sticky top-14 z-10", LATERAL)}
            >
              Form
            </SortableTh>
            <SortableTh
              k="home_abs"
              {...{ sortKey, sortDir, onSort }}
              className={cn("sticky top-14 z-10", LATERAL, "text-center")}
            >
              Out
            </SortableTh>
            <SortableTh
              k="away_score"
              {...{ sortKey, sortDir, onSort }}
              className="sticky top-14 z-10 text-center"
            >
              Fm
            </SortableTh>
            <SortableTh
              k="away_form"
              {...{ sortKey, sortDir, onSort }}
              className={cn("sticky top-14 z-10", LATERAL)}
            >
              Form
            </SortableTh>
            <SortableTh
              k="away_abs"
              {...{ sortKey, sortDir, onSort }}
              className={cn("sticky top-14 z-10", LATERAL, "text-center")}
            >
              Out
            </SortableTh>
            <SortableTh k="away_team" {...{ sortKey, sortDir, onSort }} className="sticky top-14 z-10">
              Away
            </SortableTh>
            <SortableTh
              k="odds"
              {...{ sortKey, sortDir, onSort }}
              className="sticky top-14 z-10 text-center"
            >
              Odds H·D·A
            </SortableTh>
            <SortableTh
              k="validity"
              {...{ sortKey, sortDir, onSort }}
              className={cn("sticky top-14 z-10", LATERAL)}
            >
              Data
            </SortableTh>
            <SortableTh
              k="value_home"
              {...{ sortKey, sortDir, onSort }}
              className="sticky top-14 z-10 text-center"
            >
              Val H
            </SortableTh>
            <SortableTh
              k="value_away"
              {...{ sortKey, sortDir, onSort }}
              className="sticky top-14 z-10 text-center"
            >
              Val A
            </SortableTh>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((m) => {
            const open = m.id === selectedId;
            return (
              <Fragment key={String(m.id)}>
                <TableRow
                  tabIndex={0}
                  role="button"
                  aria-expanded={open}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onToggle(m.id);
                    }
                  }}
                  onClick={() => onToggle(m.id)}
                  className={cn(
                    "cursor-pointer border-b border-border/60 outline-none focus-visible:bg-accent/40",
                    open ? "bg-muted/40" : "hover:bg-muted/30",
                  )}
                >
                  <TableCell>
                    <LeagueBadge league={m.league} />
                  </TableCell>
                  <TableCell className={cn("whitespace-nowrap text-xs text-muted-foreground", LATERAL)}>
                    {m.date_short}
                  </TableCell>
                  <TableCell className="max-w-[9rem] truncate font-semibold">
                    {m.home.team}
                  </TableCell>
                  <TableCell className="text-center">
                    <span className={cn("text-lg font-extrabold tabular-nums", scoreTextClass(m.home.score))}>
                      {Math.round(m.home.score)}
                    </span>
                  </TableCell>
                  <TableCell className={LATERAL}>
                    <FormBoxes form={m.home.form_string} />
                  </TableCell>
                  <TableCell className={cn("text-center", LATERAL)}>
                    <span
                      className={cn(
                        "rounded-md px-1.5 py-0.5 text-[11px] font-semibold tabular-nums",
                        absencesChipClass(m.home.absent_count),
                      )}
                    >
                      {m.home.absent_count}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span className={cn("text-lg font-extrabold tabular-nums", scoreTextClass(m.away.score))}>
                      {Math.round(m.away.score)}
                    </span>
                  </TableCell>
                  <TableCell className={LATERAL}>
                    <FormBoxes form={m.away.form_string} />
                  </TableCell>
                  <TableCell className={cn("text-center", LATERAL)}>
                    <span
                      className={cn(
                        "rounded-md px-1.5 py-0.5 text-[11px] font-semibold tabular-nums",
                        absencesChipClass(m.away.absent_count),
                      )}
                    >
                      {m.away.absent_count}
                    </span>
                  </TableCell>
                  <TableCell className="max-w-[9rem] truncate text-right font-semibold">
                    {m.away.team}
                  </TableCell>
                  <TableCell className="text-center">
                    <OddsCell m={m} />
                  </TableCell>
                  <TableCell className={LATERAL}>
                    <SourceDots m={m} />
                  </TableCell>
                  <TableCell className="text-center">
                    <ValueEdgeBadge m={m} side="home" />
                  </TableCell>
                  <TableCell className="text-center">
                    <ValueEdgeBadge m={m} side="away" />
                  </TableCell>
                </TableRow>
                {open && (
                  <TableRow className="border-b border-border/60 hover:bg-transparent">
                    <TableCell colSpan={COLS} className="p-0">
                      <MatchDetail m={m} rollingWindow={rollingWindow} />
                    </TableCell>
                  </TableRow>
                )}
              </Fragment>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
