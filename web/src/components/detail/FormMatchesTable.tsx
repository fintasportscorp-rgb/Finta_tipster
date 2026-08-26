import type { FormMatch } from "@/types";
import SectionTitle from "./SectionTitle";

const RESULT_CLASS: Record<string, string> = {
  W: "text-success",
  D: "text-warning",
  L: "text-destructive",
};

const TYPE_LABEL: Record<string, string> = {
  league: "L",
  friendly: "F",
  prev_season: "S",
};

const TYPE_CLASS: Record<string, string> = {
  league: "bg-muted text-muted-foreground",
  friendly: "bg-primary/10 text-primary",
  prev_season: "bg-warning/15 text-warning",
};

export default function FormMatchesTable({ team, matches }: { team: string; matches?: FormMatch[] }) {
  if (!matches || matches.length === 0) {
    return (
      <div>
        <SectionTitle>{team}</SectionTitle>
        <p className="text-xs text-muted-foreground">No form data</p>
      </div>
    );
  }
  return (
    <div>
      <SectionTitle right={`${matches.length} recent`}>{team}</SectionTitle>
      <div className="overflow-x-auto scrollbar-thin rounded-lg border">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="border-b bg-muted/40 text-left text-[10px] uppercase tracking-wide text-muted-foreground">
              <th className="px-2 py-1.5 font-semibold">Date</th>
              <th className="px-2 py-1.5 font-semibold">H/A</th>
              <th className="px-2 py-1.5 font-semibold">Opponent</th>
              <th className="px-2 py-1.5 text-center font-semibold">Score</th>
              <th className="px-2 py-1.5 text-center font-semibold">xG</th>
              <th className="px-2 py-1.5 text-center font-semibold">R</th>
              <th className="px-2 py-1.5 text-center font-semibold">T</th>
            </tr>
          </thead>
          <tbody>
            {matches.map((m, i) => (
              <tr key={i} className="border-b border-border/50 last:border-0">
                <td className="whitespace-nowrap px-2 py-1.5 tabular-nums text-muted-foreground">
                  {m.date}
                </td>
                <td className="px-2 py-1.5">
                  <span
                    className={
                      m.home_away === "H"
                        ? "rounded bg-secondary px-1 text-[10px] font-bold"
                        : "rounded bg-accent px-1 text-[10px] font-bold text-accent-foreground"
                    }
                  >
                    {m.home_away}
                  </span>
                </td>
                <td className="max-w-[9rem] truncate whitespace-nowrap px-2 py-1.5 font-medium">
                  {m.opponent}
                </td>
                <td className="whitespace-nowrap px-2 py-1.5 text-center font-semibold tabular-nums">
                  {m.gf}–{m.ga}
                </td>
                <td className="whitespace-nowrap px-2 py-1.5 text-center tabular-nums text-muted-foreground">
                  {m.xg != null ? `${m.xg.toFixed(1)}·${m.xga?.toFixed(1) ?? "–"}` : "–"}
                </td>
                <td
                  className={`px-2 py-1.5 text-center font-extrabold ${RESULT_CLASS[m.result] ?? ""}`}
                >
                  {m.result}
                </td>
                <td className="px-2 py-1.5 text-center">
                  <span
                    className={`inline-grid h-4 w-4 place-items-center rounded text-[9px] font-bold ${
                      TYPE_CLASS[m.type] ?? TYPE_CLASS.league
                    }`}
                    title={m.type}
                  >
                    {TYPE_LABEL[m.type] ?? "L"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
