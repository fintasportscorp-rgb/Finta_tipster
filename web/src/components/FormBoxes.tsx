const COLOR: Record<string, string> = {
  W: "bg-good text-white",
  D: "bg-warn text-black/80",
  L: "bg-bad text-white",
};

export default function FormBoxes({
  form,
  mini,
}: {
  form: string[] | undefined;
  mini?: boolean;
}) {
  const size = mini ? "w-[18px] h-[18px] text-[9px]" : "w-[22px] h-[22px] text-[10px]";
  if (!form || form.length === 0) {
    return (
      <div className={`${size} rounded grid place-items-center bg-border text-dimmer font-bold`}>
        -
      </div>
    );
  }
  return (
    <div className="flex gap-[3px]">
      {form.map((r, i) => (
        <div
          key={i}
          className={`${size} rounded grid place-items-center font-bold ${COLOR[r] ?? "bg-border text-dimmer"}`}
        >
          {r}
        </div>
      ))}
    </div>
  );
}
