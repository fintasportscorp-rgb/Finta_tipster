import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";
import type { Dashboard } from "@/types";

export default function Header({ data }: { data: Dashboard | null }) {
  const { theme, toggle } = useTheme();
  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-primary to-[color:hsl(var(--primary)/0.6)] shadow-sm">
            <svg viewBox="0 0 24 24" className="h-4.5 w-4.5 h-5 w-5 p-0.5" fill="none" aria-hidden>
              <path
                d="M3 17l4-6 4 3 5-8 5 5"
                stroke="currentColor"
                strokeWidth="2.4"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-white dark:text-primary-foreground"
              />
            </svg>
          </div>
          <div className="min-w-0 leading-tight">
            <h1 className="truncate text-sm font-bold sm:text-base">
              Finta Tipster
              <span className="ml-1.5 hidden text-xs font-medium text-muted-foreground sm:inline">
                Big 5 Match Form
              </span>
            </h1>
            <p className="hidden truncate text-[11px] text-muted-foreground xs:block sm:hidden md:block">
              {data ? `${data.matches.length} matches · updated ${data.generated_at}` : "Loading…"}
            </p>
          </div>
        </div>
        <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
          {theme === "dark" ? <Sun className="!size-4" /> : <Moon className="!size-4" />}
        </Button>
      </div>
    </header>
  );
}
