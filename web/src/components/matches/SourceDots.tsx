import type { Match } from "@/types";
import { SOURCES, validityClass } from "@/lib/format";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export default function SourceDots({
  m,
  showFraction = true,
  className,
}: {
  m: Match;
  showFraction?: boolean;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex gap-0.5">
            {SOURCES.map((s) => (
              <span
                key={s.key}
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  m.sources?.[s.key] ? "bg-success" : "bg-border",
                )}
              />
            ))}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p className="font-medium">Data sources</p>
          <ul className="mt-0.5 space-y-0">
            {SOURCES.map((s) => (
              <li key={s.key} className={m.sources?.[s.key] ? "" : "opacity-50"}>
                {m.sources?.[s.key] ? "✓" : "✕"} {s.label}
              </li>
            ))}
          </ul>
        </TooltipContent>
      </Tooltip>
      {showFraction && (
        <span
          className={cn("text-xs font-bold tabular-nums", validityClass(m.validity, m.validity_total))}
        >
          {m.validity}/{m.validity_total}
        </span>
      )}
    </div>
  );
}
