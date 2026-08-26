import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export default function SectionTitle({
  children,
  right,
  className,
}: {
  children: ReactNode;
  right?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-2 flex items-baseline justify-between gap-2", className)}>
      <h4 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        {children}
      </h4>
      {right && <div className="text-[11px] text-muted-foreground">{right}</div>}
    </div>
  );
}
