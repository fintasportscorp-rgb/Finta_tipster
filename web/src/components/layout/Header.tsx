import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";
import type { Dashboard } from "@/types";

export default function Header({ data }: { data: Dashboard | null }) {
  const { theme, toggle } = useTheme();
  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 w-full max-w-[1760px] items-center justify-between gap-3 px-3 sm:px-4">
        <div className="flex min-w-0 items-center gap-2.5">
          <img
            src="/finta_logo.png"
            alt="Finta"
            className="h-8 w-8 shrink-0 rounded-lg object-contain"
          />
          <div className="min-w-0 leading-tight">
            <h1 className="truncate text-sm font-bold sm:text-base">
              Tipster
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
