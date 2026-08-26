import type { Absence } from "@/types";
import SectionTitle from "./SectionTitle";

function statusBadge(type: string | undefined, status: string | undefined) {
  const raw = (type || status || "").split("(")[0].trim();
  const lower = raw.toLowerCase();
  if (lower.startsWith("injur"))
    return { label: raw || "Injured", cls: "bg-destructive/15 text-destructive" };
  if (lower.startsWith("susp"))
    return { label: raw || "Suspended", cls: "bg-warning/15 text-warning" };
  if (lower.includes("loan")) return { label: raw || "Loaned", cls: "bg-primary/10 text-primary" };
  if (lower.startsWith("int"))
    return { label: raw || "International", cls: "bg-success/15 text-success" };
  if (lower.startsWith("not"))
    return { label: raw || "Not eligible", cls: "bg-accent text-accent-foreground" };
  return { label: raw || "Unknown", cls: "bg-muted text-muted-foreground" };
}

export default function AbsencesList({
  team,
  absences,
}: {
  team: string;
  absences?: Absence[];
}) {
  const count = absences?.length ?? 0;
  return (
    <div>
      <SectionTitle right={count > 0 ? `${count} out` : undefined}>Absences — {team}</SectionTitle>
      {count === 0 ? (
        <p className="text-xs text-success/90">Full squad available</p>
      ) : (
        <ul className="divide-y divide-border/50 rounded-lg border">
          {absences!.slice(0, 12).map((a, i) => {
            const b = statusBadge(a.type, a.status);
            return (
              <li key={i} className="flex items-center justify-between gap-2 px-2 py-1.5 text-xs">
                <span className="min-w-0 truncate">
                  <span className="font-semibold">{a.player}</span>{" "}
                  <span className="text-[10px] text-muted-foreground">{a.position}</span>
                </span>
                <span className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide ${b.cls}`}>
                  {b.label}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
