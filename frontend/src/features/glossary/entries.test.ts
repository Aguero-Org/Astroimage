import { describe, expect, it } from "vitest";
import { filterGlossaryEntries, GLOSSARY_ENTRIES } from "./entries";

describe("filterGlossaryEntries", () => {
  it("returns all entries when the query is empty", () => {
    expect(filterGlossaryEntries(GLOSSARY_ENTRIES, "  ")).toHaveLength(
      GLOSSARY_ENTRIES.length,
    );
  });

  it("filters by name", () => {
    const found = filterGlossaryEntries(GLOSSARY_ENTRIES, "FWHM");
    expect(found.map((entry) => entry.id)).toEqual(["fwhm"]);
  });
});
