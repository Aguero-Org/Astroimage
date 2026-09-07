import { create } from "zustand";
import {
  applyPalette,
  DEFAULT_PALETTE_ID,
  isPaletteId,
  PALETTE_STORAGE_KEY,
  type PaletteId,
} from "./palettes";
import {
  applyThemeClass,
  readStoredTheme,
  resolveTheme,
  THEME_STORAGE_KEY,
  type Theme,
} from "./theme";

type ThemeState = {
  theme: Theme;
  paletteId: PaletteId;
  setTheme: (theme: Theme) => void;
  setPalette: (paletteId: PaletteId) => void;
  toggleTheme: () => void;
};

function currentTheme(): Theme {
  if (typeof document === "undefined") {
    return "light";
  }
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: currentTheme(),
  paletteId: DEFAULT_PALETTE_ID,
  setTheme: (theme) => {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
    applyThemeClass(theme);
    set({ theme });
  },
  setPalette: (paletteId) => {
    localStorage.setItem(PALETTE_STORAGE_KEY, paletteId);
    applyPalette(paletteId);
    set({ paletteId });
  },
  toggleTheme: () => {
    get().setTheme(get().theme === "dark" ? "light" : "dark");
  },
}));

export function hydrateTheme(): void {
  const theme = resolveTheme(readStoredTheme());
  applyThemeClass(theme);
  const storedPalette = localStorage.getItem(PALETTE_STORAGE_KEY);
  const paletteId = isPaletteId(storedPalette)
    ? storedPalette
    : DEFAULT_PALETTE_ID;
  applyPalette(paletteId);
  useThemeStore.setState({ theme, paletteId });
}
