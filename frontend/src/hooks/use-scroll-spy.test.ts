import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useScrollSpy } from "./use-scroll-spy";

describe("useScrollSpy", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    vi.restoreAllMocks();
  });

  it("tracks the last heading that crossed the offset", () => {
    document.body.innerHTML = `
      <article id="fits"></article>
      <article id="fwhm"></article>
    `;
    const fits = document.getElementById("fits");
    const fwhm = document.getElementById("fwhm");
    vi.spyOn(fits as HTMLElement, "getBoundingClientRect").mockReturnValue({
      top: -40,
    } as DOMRect);
    vi.spyOn(fwhm as HTMLElement, "getBoundingClientRect").mockReturnValue({
      top: 200,
    } as DOMRect);

    const { result } = renderHook(() =>
      useScrollSpy(["fits", "fwhm"], { offsetPx: 96 }),
    );
    expect(result.current).toBe("fits");

    vi.spyOn(fwhm as HTMLElement, "getBoundingClientRect").mockReturnValue({
      top: 40,
    } as DOMRect);
    act(() => {
      window.dispatchEvent(new Event("scroll"));
    });
    expect(result.current).toBe("fwhm");
  });

  it("selects the last id when the page is scrolled to the end", () => {
    document.body.innerHTML = `
      <article id="fits"></article>
      <article id="fwhm"></article>
    `;
    vi.spyOn(document.documentElement, "scrollHeight", "get").mockReturnValue(
      2000,
    );
    vi.spyOn(window, "innerHeight", "get").mockReturnValue(800);
    vi.spyOn(window, "scrollY", "get").mockReturnValue(1200);

    const { result } = renderHook(() =>
      useScrollSpy(["fits", "fwhm"], { offsetPx: 96 }),
    );
    act(() => {
      window.dispatchEvent(new Event("scroll"));
    });
    expect(result.current).toBe("fwhm");
  });
});
