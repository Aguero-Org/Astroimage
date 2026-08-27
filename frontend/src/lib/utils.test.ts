import { describe, expect, it } from "vitest";
import { z } from "zod";
import { cn } from "./utils";

describe("cn", () => {
  it("merges tailwind classes", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });
});

describe("zod", () => {
  it("is available for form schemas", () => {
    const schema = z.object({ name: z.string() });
    expect(schema.parse({ name: "astroimage" })).toEqual({
      name: "astroimage",
    });
  });
});
