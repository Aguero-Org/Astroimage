import { describe, expect, it } from "vitest";
import { ApiError } from "./api-client";
import { queryClient } from "./query-client";

function shouldRetry(error: Error, failureCount: number): boolean {
  const retry = queryClient.getDefaultOptions().queries?.retry;
  if (typeof retry !== "function") {
    throw new Error("expected retry to be a function");
  }
  return retry(failureCount, error) as boolean;
}

describe("queryClient", () => {
  it("does not refetch when the window or tab is focused again", () => {
    const queries = queryClient.getDefaultOptions().queries;
    expect(queries?.refetchOnWindowFocus).toBe(false);
    expect(queries?.refetchOnReconnect).not.toBe(false);
  });

  it("never retries client errors", () => {
    expect(shouldRetry(new ApiError(404, "Not Found", null), 0)).toBe(false);
  });

  it("retries server errors at most once", () => {
    expect(shouldRetry(new ApiError(500, "Server Error", null), 0)).toBe(true);
    expect(shouldRetry(new ApiError(500, "Server Error", null), 1)).toBe(false);
  });

  it("retries network errors at most once", () => {
    expect(shouldRetry(new Error("network down"), 0)).toBe(true);
    expect(shouldRetry(new Error("network down"), 1)).toBe(false);
  });
});
