import { describe, expect, it } from "vitest";
import type { SourceDetectionResponse } from "@/api/generated/model";
import { customFetch } from "@/lib/api-client";
import { MOCK_POINT_SOURCE } from "@/mocks/data/image";

type ListRecordsResponse = {
  records: { record_id: string; name: string }[];
};

describe("image mock contract", () => {
  it("GET /image returns all records as { records: [...] }", async () => {
    const result = await customFetch<{
      data: ListRecordsResponse;
      status: number;
    }>("/image");

    expect(result.status).toBe(200);
    expect(result.data.records.length).toBe(4);
  });

  it("GET /image?cuerpo_celeste=orion filters records", async () => {
    const result = await customFetch<{
      data: ListRecordsResponse;
      status: number;
    }>("/image?cuerpo_celeste=orion");

    expect(result.data.records).toHaveLength(1);
    expect(result.data.records[0]?.record_id).toBe("m42");
  });

  it("GET /image/search?query=orion returns a single record_id", async () => {
    const result = await customFetch<{
      data: { record_id: string };
      status: number;
    }>("/image/search?query=orion");

    expect(result.status).toBe(200);
    expect(result.data.record_id).toBe("m42");
  });

  it("GET /image/:id/info returns image metadata", async () => {
    const result = await customFetch<{
      data: { source_name: string; hdus: { selected: number } };
      status: number;
    }>("/image/m31/info");

    expect(result.status).toBe(200);
    expect(result.data.source_name).toBe("M31 - Andromeda Galaxy");
  });

  it("GET /image/:id/info returns 404 for unknown id", async () => {
    await expect(customFetch("/image/unknown/info")).rejects.toSatisfy(
      (error: unknown) => {
        return (
          error instanceof Error && "status" in error && error.status === 404
        );
      },
    );
  });

  it("GET /image/:id/sources returns canned point detections", async () => {
    const result = await customFetch<{
      data: SourceDetectionResponse;
      status: number;
    }>("/image/m31/sources");

    expect(result.status).toBe(200);
    expect(result.data.summary.point_count).toBe(1);
    expect(result.data.point_sources?.[0]).toEqual(MOCK_POINT_SOURCE);
  });

  it("GET /image/:id/sources ignores detection query params", async () => {
    const result = await customFetch<{
      data: SourceDetectionResponse;
      status: number;
    }>("/image/m31/sources?fwhm=99&sigma=99&max_sources=1");

    expect(result.data.point_sources?.[0]).toEqual(MOCK_POINT_SOURCE);
  });

  it("GET /image/:id/sources returns 404 for unknown id", async () => {
    await expect(customFetch("/image/unknown/sources")).rejects.toSatisfy(
      (error: unknown) => {
        return (
          error instanceof Error && "status" in error && error.status === 404
        );
      },
    );
  });

  it("GET /image/:id returns a PNG blob", async () => {
    const result = await customFetch<{
      data: Blob;
      status: number;
    }>("/image/m42");

    expect(result.status).toBe(200);
    expect(result.data.size).toBeGreaterThan(0);
    expect(result.data.type).toBe("image/png");
  });

  it("GET /image/:id returns 404 for unknown id", async () => {
    await expect(customFetch("/image/unknown")).rejects.toSatisfy(
      (error: unknown) => {
        return (
          error instanceof Error && "status" in error && error.status === 404
        );
      },
    );
  });
});
