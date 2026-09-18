import { describe, expect, it } from "vitest";
import { queryClient } from "./query-client";

describe("queryClient", () => {
  it("does not refetch when the window or tab is focused again", () => {
    const queries = queryClient.getDefaultOptions().queries;
    expect(queries?.refetchOnWindowFocus).toBe(false);
    expect(queries?.refetchOnReconnect).toBe(false);
  });
});
