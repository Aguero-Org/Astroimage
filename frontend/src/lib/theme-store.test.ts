import { afterEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_PALETTE_ID, PALETTE_STORAGE_KEY, PALETTES } from "./palettes";
import { THEME_STORAGE_KEY } from "./theme";
import { hydrateTheme, useThemeStore } from "./theme-store";

const originalMatchMedia = window.matchMedia;

function setPrefersDark(matches: boolean): void {
  window.matchMedia = vi.fn((query: string) => ({
    matches,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}

function paletteVariable(index: number): string {
  return document.documentElement.style.getPropertyValue(`--palette-${index}`);
}

afterEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove("dark");
  window.matchMedia = originalMatchMedia;
  useThemeStore.setState({
    theme: "light",
    paletteId: DEFAULT_PALETTE_ID,
  });
});

describe("hydrateTheme", () => {
  it("uses the system preference and the default palette when nothing is stored", () => {
    setPrefersDark(false);

    hydrateTheme();

    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(useThemeStore.getState().theme).toBe("light");
    expect(useThemeStore.getState().paletteId).toBe(DEFAULT_PALETTE_ID);
    expect(paletteVariable(1)).toBe(PALETTES[DEFAULT_PALETTE_ID].swatches[0]);
  });

  it("honours a stored theme and ignores an unknown palette", () => {
    localStorage.setItem(THEME_STORAGE_KEY, "dark");
    localStorage.setItem(PALETTE_STORAGE_KEY, "nope");
    setPrefersDark(false);

    hydrateTheme();

    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(useThemeStore.getState().theme).toBe("dark");
    expect(useThemeStore.getState().paletteId).toBe(DEFAULT_PALETTE_ID);
  });
});

describe("useThemeStore", () => {
  it("persists and applies a new theme", () => {
    useThemeStore.getState().setTheme("dark");

    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(useThemeStore.getState().theme).toBe("dark");
  });

  it("persists and applies a palette", () => {
    useThemeStore.getState().setPalette("cosmic");

    expect(localStorage.getItem(PALETTE_STORAGE_KEY)).toBe("cosmic");
    expect(useThemeStore.getState().paletteId).toBe("cosmic");
    PALETTES.cosmic.swatches.forEach((hex, index) => {
      expect(paletteVariable(index + 1)).toBe(hex);
    });
  });

  it("toggles between light and dark", () => {
    useThemeStore.getState().toggleTheme();
    expect(useThemeStore.getState().theme).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    useThemeStore.getState().toggleTheme();
    expect(useThemeStore.getState().theme).toBe("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("initializes the store from the document class", async () => {
    document.documentElement.classList.add("dark");
    vi.resetModules();
    const darkModule = await import("./theme-store");
    expect(darkModule.useThemeStore.getState().theme).toBe("dark");

    document.documentElement.classList.remove("dark");
    vi.resetModules();
    const lightModule = await import("./theme-store");
    expect(lightModule.useThemeStore.getState().theme).toBe("light");
  });
});
