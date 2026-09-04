import { describe, expect, it, vi } from "vitest";
import { renderHookWithQuery } from "@/test/render";
import { useImageRecords } from "./api";

describe("useImageRecords", () => {
  it("returns filtered records for a query", async () => {
    const { result } = renderHookWithQuery(() => useImageRecords("orion"));

    await vi.waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.status).toBe(200);
    const records =
      result.current.data?.status === 200
        ? result.current.data.data.records
        : [];
    expect(records).toHaveLength(1);
    expect(records[0]?.record_id).toBe("m42");
  });

  it("returns all records when query is empty", async () => {
    const { result } = renderHookWithQuery(() => useImageRecords(""));

    await vi.waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.status).toBe(200);
    const records =
      result.current.data?.status === 200
        ? result.current.data.data.records
        : [];
    expect(records).toHaveLength(4);
  });

  it("returns empty records for no matches", async () => {
    const { result } = renderHookWithQuery(() =>
      useImageRecords("nonexistent"),
    );

    await vi.waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.status).toBe(200);
    const records =
      result.current.data?.status === 200
        ? result.current.data.data.records
        : [];
    expect(records).toEqual([]);
  });
});
