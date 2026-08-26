import { cn } from "@/lib/utils";

const RESULT_CLASS: Record<string, string> = {
  W: "bg-success/20 text-success",
  D: "bg-warning/20 text-warning",
  L: "bg-destructive/20 text-destructive",
};

export default function FormBoxes({
  form,
  className,
  boxClass,
}: {
  form: string[] | undefined;
  className?: string;
  boxClass?: string;
}) {
  const size = boxClass ?? "h-5 w-5 text-[10px]";
  if (!form || form.length === 0) {
    return (
      <div
        className={cn(
          size,
          "grid place-items-center rounded-md bg-muted font-bold text-muted-foreground",
          className,
        )}
      >
        –
      </div>
    );
  }
  return (
    <div className={cn("flex gap-0.5", className)}>
      {form.map((r, i) => (
        <div
          key={i}
          title={r === "W" ? "Win" : r === "D" ? "Draw" : r === "L" ? "Loss" : r}
          className={cn(
            size,
            "grid place-items-center rounded-md font-bold tabular-nums",
            RESULT_CLASS[r] ?? "bg-muted text-muted-foreground",
          )}
        >
          {r}
        </div>
      ))}
    </div>
  );
}
