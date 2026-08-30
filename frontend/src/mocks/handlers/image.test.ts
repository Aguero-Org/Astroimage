import { describe, expect, it } from "vitest";
import { customFetch } from "@/lib/api-client";

type ImageSummary = {
  id: string;
  name: string;
  object: string;
};

describe("image mock contract", () => {
  it("GET /image returns the full list when no query", async () => {
    const result = await customFetch<{
      data: ImageSummary[];
      status: number;
    }>("/image");

    expect(result.status).toBe(200);
    expect(result.data.length).toBeGreaterThan(0);
    expect(result.data[0]?.id).toBeDefined();
  });

  it("GET /image?query=m31 filters by query", async () => {
    const result = await customFetch<{
      data: ImageSummary[];
      status: number;
    }>("/image?query=m31");

    expect(result.data).toHaveLength(1);
    expect(result.data[0]?.object).toBe("M31");
  });

  it("GET /image/search?query=orion returns matching images", async () => {
    const result = await customFetch<{
      data: ImageSummary[];
      status: number;
    }>("/image/search?query=orion");

    expect(result.data).toHaveLength(1);
    expect(result.data[0]?.id).toBe("m42");
  });

  it("GET /image/:id/info returns image metadata", async () => {
    const result = await customFetch<{
      data: ImageSummary & { pixelScale: number };
      status: number;
    }>("/image/m31/info");

    expect(result.status).toBe(200);
    expect(result.data.id).toBe("m31");
    expect(result.data.pixelScale).toBeDefined();
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

  it("GET /image/:id returns binary data", async () => {
    const result = await customFetch<{
      data: { size: number };
      status: number;
    }>("/image/m42");

    expect(result.status).toBe(200);
    expect(result.data.size).toBeGreaterThan(0);
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
