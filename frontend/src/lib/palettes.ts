export const PALETTE_STORAGE_KEY = "astroimage-palette";

export type PaletteId = keyof typeof PALETTES;

export const PALETTES = {
  cosmic: {
    label: "Cósmico",
    swatches: ["#f2f2f7", "#858ae3", "#613dc1", "#1c1c1e", "#000000"],
  },
  nebula: {
    label: "Nebula",
    swatches: ["#97dffc", "#858ae3", "#613dc1", "#4e148c", "#2c0735"],
  },
} as const satisfies Record<
  string,
  { label: string; swatches: readonly [string, string, string, string, string] }
>;

export const DEFAULT_PALETTE_ID: PaletteId = "cosmic";

export function isPaletteId(value: string | null): value is PaletteId {
  return value !== null && value in PALETTES;
}

export function applyPalette(paletteId: PaletteId): void {
  const { swatches } = PALETTES[paletteId];
  swatches.forEach((hex, index) => {
    document.documentElement.style.setProperty(`--palette-${index + 1}`, hex);
  });
}
