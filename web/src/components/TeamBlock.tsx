import type { TeamData } from "../types";
import { scoreColor } from "../lib/format";
import FormBoxes from "./FormBoxes";
import MetricBars from "./MetricBars";

export default function TeamBlock({ t }: { t: TeamData }) {
  const bd = t.form_breakdown;
  const parts: JSX.Element[] = [];
  if (bd?.league) parts.push(<span key="l" className="text-good">{bd.league}L</span>);
  if (bd?.friendly) parts.push(<span key="f" className="text-info">{bd.friendly}F</span>);
  if (bd?.prev_season) parts.push(<span key="s" className="text-warn">{bd.prev_season}S</span>);

  return (
    <div className="bg-card2 border border-border2 rounded-[10px] p-3 sm:p-4">
      <div className="text-[15px] font-bold mb-0.5">{t.team}</div>
      <div className={`text-3xl sm:text-4xl font-extrabold leading-none ${scoreColor(t.score)}`}>
        {Math.round(t.score)}
      </div>
      {parts.length > 0 && (
        <div className="text-center text-[10px] text-dim mb-1 mt-1 flex justify-center gap-2">
          <span>Form:</span> {parts}
        </div>
      )}
      <div className="my-2">
        <FormBoxes form={t.form_string} />
      </div>
      <MetricBars c={t.components} />
      {t.last_formation && (
        <div className="text-center mt-1.5 text-xs text-dim">
          Last: <strong className="text-accent">{t.last_formation}</strong>
        </div>
      )}
    </div>
  );
}
