import { leagueColor } from "@/lib/format";
import { cn } from "@/lib/utils";

export default function LeagueBadge({
  league,
  className,
}: {
  league: string;
  className?: string;
}) {
  const color = leagueColor(league);
  return (
    <span
      className={cn(
        "inline-flex items-center whitespace-nowrap rounded-md px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide",
        className,
      )}
      style={{ color, backgroundColor: `${color}1f` }}
    >
      {league}
    </span>
  );
}
