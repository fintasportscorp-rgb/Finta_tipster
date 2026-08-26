import type { Tip } from "@/types";
import SectionTitle from "./SectionTitle";
import { cn } from "@/lib/utils";

const FAVOR_CLASS: Record<string, string> = {
  home: "bg-success/15 text-success",
  away: "bg-destructive/15 text-destructive",
  draw: "bg-warning/15 text-warning",
  neutral: "bg-warning/15 text-warning",
};

export default function TipsPanel({ tips }: { tips?: Tip[] }) {
  const list = tips ?? [];
  return (
    <div>
      <SectionTitle right={`${list.length} sources`}>Expert tips</SectionTitle>
      {list.length === 0 ? (
        <p className="text-xs text-muted-foreground">No tipster data</p>
      ) : (
        <ul className="divide-y divide-border/50 rounded-lg border">
          {list.slice(0, 10).map((t, i) => (
            <li key={i} className="flex items-start justify-between gap-3 px-2.5 py-2 text-xs">
              <span className="w-20 shrink-0 truncate pt-px text-[11px] font-semibold text-primary sm:w-28">
                {t.website}
              </span>
              <span className="flex-1 leading-snug">{t.tip}</span>
              <span
                className={cn(
                  "shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide",
                  FAVOR_CLASS[t.favor] ?? "bg-muted text-muted-foreground",
                )}
              >
                {t.favor}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
