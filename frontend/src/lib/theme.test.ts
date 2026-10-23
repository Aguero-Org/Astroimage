import { afterEach, describe, expect, it, vi } from "vitest";
import {
  applyThemeClass,
  readStoredTheme,
  resolveTheme,
  THEME_STORAGE_KEY,
} from "./theme";

const originalMatchMedia = window.matchMedia;
let lastMediaQuery = "";

function setPrefersDark(matches: boolean): void {
  window.matchMedia = vi.fn((query: string) => {
    lastMediaQuery = query;
    return {
      matches,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    };
  }) as unknown as typeof window.matchMedia;
}

afterEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove("dark");
  window.matchMedia = originalMatchMedia;
});

describe("readStoredTheme", () => {
  it("returns the stored theme when it is light or dark", () => {
    localStorage.setItem(THEME_STORAGE_KEY, "dark");
    expect(readStoredTheme()).toBe("dark");

    localStorage.setItem(THEME_STORAGE_KEY, "light");
    expect(readStoredTheme()).toBe("light");
  });

  it("returns null for missing or unknown values", () => {
    expect(readStoredTheme()).toBeNull();

    localStorage.setItem(THEME_STORAGE_KEY, "sepia");
    expect(readStoredTheme()).toBeNull();
  });
});

describe("resolveTheme", () => {
  it("prefers the stored theme over the system preference", () => {
    setPrefersDark(true);
    expect(resolveTheme("light")).toBe("light");

    setPrefersDark(false);
    expect(resolveTheme("dark")).toBe("dark");
  });

  it("falls back to the system preference when nothing is stored", () => {
    setPrefersDark(true);
    expect(resolveTheme(null)).toBe("dark");
    expect(lastMediaQuery).toBe("(prefers-color-scheme: dark)");

    setPrefersDark(false);
    expect(resolveTheme(null)).toBe("light");
  });
});

describe("storage key", () => {
  it("keeps the persisted key stable", () => {
    expect(THEME_STORAGE_KEY).toBe("astroimage-theme");
  });
});

describe("applyThemeClass", () => {
  it("toggles the dark class on the document element", () => {
    applyThemeClass("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    applyThemeClass("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});
