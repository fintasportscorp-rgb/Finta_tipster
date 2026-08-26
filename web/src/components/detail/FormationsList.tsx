import type { FormationHist } from "@/types";
import SectionTitle from "./SectionTitle";

export default function FormationsList({
  team,
  hist,
  radicalChanges,
}: {
  team: string;
  hist?: FormationHist[];
  radicalChanges: number;
}) {
  return (
    <div>
      <SectionTitle right={radicalChanges > 0 ? `${radicalChanges} radical changes` : "stable"}>
        Formations — {team}
      </SectionTitle>
      {!hist || hist.length === 0 ? (
        <p className="text-xs text-muted-foreground">No formation data</p>
      ) : (
        <div className="flex flex-wrap gap-1">
          {hist.slice(0, 10).map((f, i) => (
            <span
              key={i}
              className="rounded-md border bg-muted/40 px-1.5 py-0.5 text-[11px] font-semibold tabular-nums"
            >
              {f.formation}
              <span className="ml-1 text-[9px] font-normal text-muted-foreground">MW{f.matchday}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
