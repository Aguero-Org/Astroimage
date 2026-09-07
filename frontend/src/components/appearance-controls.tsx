import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PALETTES, type PaletteId } from "@/lib/palettes";
import { useThemeStore } from "@/lib/theme-store";
import { ThemeToggle } from "./theme-toggle";

const PALETTE_IDS = Object.keys(PALETTES) as PaletteId[];

export function AppearanceControls() {
  const paletteId = useThemeStore((state) => state.paletteId);
  const setPalette = useThemeStore((state) => state.setPalette);
  const swatches = PALETTES[paletteId].swatches;

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1" aria-hidden="true">
        {swatches.map((hex) => (
          <span
            key={hex}
            className="size-3 rounded-full border border-border"
            style={{ backgroundColor: hex }}
          />
        ))}
      </div>
      {PALETTE_IDS.length > 1 ? (
        <Select
          value={paletteId}
          onValueChange={(value) => {
            setPalette(value as PaletteId);
          }}
        >
          <SelectTrigger
            data-testid="palette-switcher"
            className="h-8 w-[8.5rem]"
            aria-label="Paleta de color"
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PALETTE_IDS.map((id) => (
              <SelectItem key={id} value={id}>
                {PALETTES[id].label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : null}
      <ThemeToggle />
    </div>
  );
}
