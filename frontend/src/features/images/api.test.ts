import { describe, expect, it, vi } from "vitest";
import { renderHookWithQuery } from "@/test/render";
import { useImageSearch } from "./api";

describe("useImageSearch", () => {
  it("returns matching images for a query", async () => {
    const { result } = renderHookWithQuery(() => useImageSearch("orion"));

    await vi.waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0]?.id).toBe("m42");
  });

  it("is not enabled when query is empty", () => {
    const { result } = renderHookWithQuery(() => useImageSearch(""));

    expect(result.current.isPending).toBe(true);
    expect(result.current.data).toBeUndefined();
  });

  it("returns empty array for no matches", async () => {
    const { result } = renderHookWithQuery(() => useImageSearch("nonexistent"));

    await vi.waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual([]);
  });
});
