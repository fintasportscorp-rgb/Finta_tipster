import type { Match } from "@/types";
import { EDGE_TIER_CLASS, edgeTier, getValueEdge } from "@/lib/format";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export default function ValueEdgeBadge({
  m,
  side,
}: {
  m: Match;
  side: "home" | "away";
}) {
  const edge = getValueEdge(m, side);
  const vbs = (m.value_bets || []).filter((v) => v.side === side);
  if (edge === null || !vbs.length)
    return <span className="text-xs text-muted-foreground/60">—</span>;
  const best = vbs.reduce((a, b) => (b.edge > a.edge ? b : a));
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className={`inline-block cursor-default rounded-md px-1.5 py-0.5 text-[10px] font-extrabold tabular-nums ${EDGE_TIER_CLASS[edgeTier(edge)]}`}
        >
          +{edge}%
        </span>
      </TooltipTrigger>
      <TooltipContent>
        <p className="font-semibold">
          {best.team} @ {best.odds}
        </p>
        <p>
          Form {best.form_prob}% vs implied {best.implied_prob}%
        </p>
      </TooltipContent>
    </Tooltip>
  );
}
