import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useScrollSpy } from "./use-scroll-spy";

describe("useScrollSpy", () => {
  afterEach(() => {
    document.body.innerHTML = "";
    vi.restoreAllMocks();
  });

  it("selects the first article still visible below the offset", () => {
    document.body.innerHTML = `
      <article id="fits"></article>
      <article id="fwhm"></article>
    `;
    const fits = document.getElementById("fits");
    const fwhm = document.getElementById("fwhm");
    vi.spyOn(fits as HTMLElement, "getBoundingClientRect").mockReturnValue({
      top: 20,
      bottom: 140,
    } as DOMRect);
    vi.spyOn(fwhm as HTMLElement, "getBoundingClientRect").mockReturnValue({
      top: 300,
      bottom: 400,
    } as DOMRect);

    const { result } = renderHook(() =>
      useScrollSpy(["fits", "fwhm"], { offsetPx: 96 }),
    );
    expect(result.current).toBe("fits");

    vi.spyOn(fits as HTMLElement, "getBoundingClientRect").mockReturnValue({
      top: -40,
      bottom: -10,
    } as DOMRect);
    vi.spyOn(fwhm as HTMLElement, "getBoundingClientRect").mockReturnValue({
      top: 40,
      bottom: 120,
    } as DOMRect);
    act(() => {
      window.dispatchEvent(new Event("scroll"));
    });
    expect(result.current).toBe("fwhm");
  });

  it("keeps the article whose end is still visible under the offset", () => {
    document.body.innerHTML = `
      <article id="fits"></article>
      <article id="fwhm"></article>
    `;
    const fits = document.getElementById("fits");
    const fwhm = document.getElementById("fwhm");
    vi.spyOn(fits as HTMLElement, "getBoundingClientRect").mockReturnValue({
      top: -10,
      bottom: 120,
    } as DOMRect);
    vi.spyOn(fwhm as HTMLElement, "getBoundingClientRect").mockReturnValue({
      top: 200,
      bottom: 260,
    } as DOMRect);

    const { result } = renderHook(() =>
      useScrollSpy(["fits", "fwhm"], { offsetPx: 96 }),
    );
    expect(result.current).toBe("fits");
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
