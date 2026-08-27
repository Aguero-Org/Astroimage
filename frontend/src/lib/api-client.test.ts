import { describe, expect, it } from "vitest";
import { customFetch } from "./api-client";

describe("customFetch", () => {
  it("calls the health endpoint through MSW", async () => {
    const result = await customFetch<{
      data: { status: string };
      status: number;
    }>("/health");
    expect(result.status).toBe(200);
    expect(result.data).toEqual({ status: "ok" });
  });
});
