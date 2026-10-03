import { describe, expect, it } from "vitest";
import { followOnQueriesEnabled } from "./workspace-queries";

describe("followOnQueriesEnabled", () => {
  it("waits until the render query has finished", () => {
    expect(followOnQueriesEnabled({ isSuccess: false, isFetching: true })).toBe(
      false,
    );
    expect(followOnQueriesEnabled({ isSuccess: true, isFetching: true })).toBe(
      false,
    );
    expect(followOnQueriesEnabled({ isSuccess: true, isFetching: false })).toBe(
      true,
    );
  });
});
