import { describe, expect, it } from "vitest";
import { homeSearchSchema } from "./home-search";

describe("homeSearchSchema", () => {
  it("keeps valid values from the URL", () => {
    expect(
      homeSearchSchema.parse({
        query: "M31",
        page: "3",
        sort: "display_name",
        order: "asc",
        cpage: "2",
        csort: "instrument",
        corder: "desc",
      }),
    ).toEqual({
      query: "M31",
      page: 3,
      sort: "display_name",
      order: "asc",
      cpage: 2,
      csort: "instrument",
      corder: "desc",
    });
  });

  it("applies defaults when values are missing", () => {
    expect(homeSearchSchema.parse({})).toEqual({
      query: "",
      page: 1,
      sort: "created_at",
      order: "desc",
      cpage: 1,
      csort: "product_filename",
      corder: "asc",
    });
  });

  it("falls back for malformed pages and sorts", () => {
    expect(
      homeSearchSchema.parse({
        page: "nope",
        sort: "not-a-field",
        order: "sideways",
        cpage: "0",
        csort: "unknown",
        corder: "up",
      }),
    ).toEqual({
      query: "",
      page: 1,
      sort: "created_at",
      order: "desc",
      cpage: 1,
      csort: "product_filename",
      corder: "asc",
    });
  });

  it("keeps stored and candidate list keys independent", () => {
    const parsed = homeSearchSchema.parse({
      page: "4",
      sort: "observed_at",
      order: "asc",
      cpage: "5",
      csort: "size_bytes",
      corder: "desc",
    });

    expect(parsed.page).toBe(4);
    expect(parsed.sort).toBe("observed_at");
    expect(parsed.cpage).toBe(5);
    expect(parsed.csort).toBe("size_bytes");
  });
});
