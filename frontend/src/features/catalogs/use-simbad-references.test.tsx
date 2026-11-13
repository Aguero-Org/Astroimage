import { waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { simbadReferencesResponse } from "@/mocks/data/simbad";
import { renderHookWithQuery } from "@/test/render";
import { server } from "@/test/server";
import { useSimbadReferences } from "./use-simbad-references";

const SIMBAD_URL = "http://localhost:8000/image/m31/simbad-references";

function captureParams() {
  let searchParams: URLSearchParams | null = null;
  server.use(
    http.get(SIMBAD_URL, ({ request }) => {
      searchParams = new URL(request.url).searchParams;
      return HttpResponse.json(simbadReferencesResponse);
    }),
  );
  return () => searchParams;
}

describe("useSimbadReferences", () => {
  it("sends the hdu and crossmatch parameters", async () => {
    const params = captureParams();
    const { result } = renderHookWithQuery(() =>
      useSimbadReferences({
        recordId: "m31",
        hdu: 2,
        detectionParams: { fwhm: 3, sigma: 5, max_sources: 50 },
        crossmatchRadiusArcsec: 6.5,
        probabilityPower: 1.5,
        enabled: true,
      }),
    );

    await waitFor(() => expect(result.current.result).toBeDefined());

    expect(params()?.get("hdu")).toBe("2");
    expect(params()?.get("fwhm")).toBe("3");
    expect(params()?.get("sigma")).toBe("5");
    expect(params()?.get("max_sources")).toBe("50");
    expect(params()?.get("crossmatch_radius_arcsec")).toBe("6.5");
    expect(params()?.get("probability_power")).toBe("1.5");
  });

  it("omits the hdu for single-plane files", async () => {
    const params = captureParams();
    const { result } = renderHookWithQuery(() =>
      useSimbadReferences({
        recordId: "m31",
        hdu: null,
        detectionParams: {},
        crossmatchRadiusArcsec: 5,
        probabilityPower: 2,
        enabled: true,
      }),
    );

    await waitFor(() => expect(result.current.result).toBeDefined());

    expect(params()?.has("hdu")).toBe(false);
    expect(params()?.get("crossmatch_radius_arcsec")).toBe("5");
    expect(params()?.get("probability_power")).toBe("2");
  });

  it("stays empty and idle while disabled", () => {
    const onRequest = vi.fn();
    server.use(
      http.get(SIMBAD_URL, () => {
        onRequest();
        return HttpResponse.json(simbadReferencesResponse);
      }),
    );
    const { result } = renderHookWithQuery(() =>
      useSimbadReferences({
        recordId: "m31",
        hdu: null,
        detectionParams: {},
        crossmatchRadiusArcsec: 5,
        probabilityPower: 2,
        enabled: false,
      }),
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.objects).toEqual([]);
    expect(onRequest).not.toHaveBeenCalled();
  });

  it("reports loading until the response arrives and refetches", async () => {
    let release: (() => void) | undefined;
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    let requests = 0;
    server.use(
      http.get(SIMBAD_URL, async () => {
        requests += 1;
        await gate;
        return HttpResponse.json(simbadReferencesResponse);
      }),
    );
    const { result } = renderHookWithQuery(() =>
      useSimbadReferences({
        recordId: "m31",
        hdu: null,
        detectionParams: {},
        crossmatchRadiusArcsec: 5,
        probabilityPower: 2,
        enabled: true,
      }),
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.objects).toEqual([]);

    release?.();
    await waitFor(() => expect(result.current.result).toBeDefined());
    expect(result.current.isLoading).toBe(false);

    result.current.refetch();
    await waitFor(() => expect(requests).toBe(2));
  });
});
