import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useThemeStore } from "@/lib/theme-store";

export function ThemeToggle() {
  const theme = useThemeStore((state) => state.theme);
  const toggleTheme = useThemeStore((state) => state.toggleTheme);
  const isDark = theme === "dark";

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      data-testid="theme-toggle"
      aria-label={isDark ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
      onClick={toggleTheme}
    >
      {isDark ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </Button>
  );
}
