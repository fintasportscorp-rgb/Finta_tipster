import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { Match } from "@/types";
import { Card } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import FormBoxes from "./FormBoxes";
import LeagueBadge from "./LeagueBadge";
import ScoreBadge from "./ScoreBadge";
import SourceDots from "./SourceDots";
import ValueEdgeBadge from "./ValueEdgeBadge";
import MatchDetail from "@/components/detail/MatchDetail";

function OddsChips({ m }: { m: Match }) {
  const o = m.odds;
  const items: [string, number | null][] = [
    ["H", o?.home ?? null],
    ["D", o?.draw ?? null],
    ["A", o?.away ?? null],
  ];
  if (!o?.home) return <span className="text-[11px] text-muted-foreground/60">No odds</span>;
  return (
    <div className="flex gap-1">
      {items.map(([label, v]) => (
        <span
          key={label}
          className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-semibold tabular-nums text-muted-foreground"
        >
          <span className="opacity-60">{label}</span> {v ?? "–"}
        </span>
      ))}
    </div>
  );
}

export default function MatchCards({
  matches,
  rollingWindow,
}: {
  matches: Match[];
  rollingWindow: number;
}) {
  return (
    <div className="space-y-2.5">
      {matches.map((m) => (
        <MatchCard key={String(m.id)} m={m} rollingWindow={rollingWindow} />
      ))}
    </div>
  );
}

function MatchCard({ m, rollingWindow }: { m: Match; rollingWindow: number }) {
  const [open, setOpen] = useState(false);
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className={cn("overflow-hidden transition-shadow", open && "shadow-md ring-1 ring-primary/30")}>
        <div className="flex items-center justify-between gap-2 border-b border-border/50 px-3 py-2">
          <div className="flex min-w-0 flex-wrap items-center gap-1.5">
            <LeagueBadge league={m.league} />
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
              {m.gameweek != null ? `GW ${m.gameweek}` : ""}
            </span>
          </div>
          <span className="whitespace-nowrap text-[11px] tabular-nums text-muted-foreground">
            {m.date_short}
          </span>
        </div>

        <CollapsibleTrigger asChild>
          <button
            className="w-full px-3 py-3 text-left outline-none transition-colors hover:bg-muted/40 focus-visible:bg-accent/40"
            aria-expanded={open}
          >
            <div className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-x-2 gap-y-2.5">
              <span className="truncate text-sm font-semibold">{m.home.team}</span>
              <FormBoxes
                form={m.home.form_string}
                boxClass="h-5 w-5 text-[9px]"
                className="hidden justify-self-end xs:flex"
              />
              <ScoreBadge score={m.home.score} size="sm" />
              <ChevronDown
                className={cn(
                  "!size-4 row-span-2 self-center justify-self-end text-muted-foreground transition-transform duration-200",
                  open && "rotate-180",
                )}
              />

              <span className="col-start-1 truncate text-sm font-semibold">{m.away.team}</span>
              <FormBoxes
                form={m.away.form_string}
                boxClass="h-5 w-5 text-[9px]"
                className="hidden justify-self-end xs:flex"
              />
              <ScoreBadge score={m.away.score} size="sm" />
            </div>
          </button>
        </CollapsibleTrigger>

        <div className="flex items-center justify-between gap-2 border-t border-border/50 px-3 py-2">
          <OddsChips m={m} />
          <div className="flex items-center gap-1.5">
            <ValueEdgeBadge m={m} side="home" />
            <ValueEdgeBadge m={m} side="away" />
            <SourceDots m={m} showFraction={false} />
          </div>
        </div>

        <CollapsibleContent className="overflow-hidden data-[state=open]:animate-accordion-down data-[state=closed]:animate-accordion-up">
          <div className="border-t border-border/50 bg-card">
            <MatchDetail m={m} rollingWindow={rollingWindow} compact />
          </div>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
