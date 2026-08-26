import { scoreChipClass } from "@/lib/format";
import { cn } from "@/lib/utils";

export default function ScoreBadge({
  score,
  size = "md",
  className,
}: {
  score: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-grid place-items-center rounded-lg font-extrabold tabular-nums leading-none",
        scoreChipClass(score),
        size === "sm" && "h-7 min-w-9 px-1.5 text-sm",
        size === "md" && "h-8 min-w-10 px-2 text-base",
        size === "lg" && "h-11 min-w-14 px-3 text-2xl sm:text-3xl",
        className,
      )}
    >
      {Math.round(score)}
    </span>
  );
}
