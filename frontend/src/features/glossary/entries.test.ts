import { describe, expect, it } from "vitest";
import { filterGlossaryEntries, GLOSSARY_ENTRIES } from "./entries";

const SOURCE_TEXT = import.meta.glob(
  [
    "../../**/*.{ts,tsx}",
    "!../../**/*.test.{ts,tsx}",
    "!../../**/entries.ts",
    "!../../**/entries-*.ts",
    "!../../api/generated/**",
  ],
  { eager: true, query: "?raw", import: "default" },
);

function linkedGlossaryIds(): Set<string> {
  const ids = new Set<string>();
  const pattern = /glossaryId\s*(?:=|:)\s*"([^"]+)"/g;
  for (const text of Object.values(SOURCE_TEXT)) {
    if (typeof text !== "string") {
      continue;
    }
    for (const match of text.matchAll(pattern)) {
      const id = match[1];
      if (id !== undefined) {
        ids.add(id);
      }
    }
  }
  return ids;
}

describe("filterGlossaryEntries", () => {
  it("returns all entries when the query is empty", () => {
    expect(filterGlossaryEntries(GLOSSARY_ENTRIES, "  ")).toHaveLength(
      GLOSSARY_ENTRIES.length,
    );
  });

  it("filters by name", () => {
    const found = filterGlossaryEntries(GLOSSARY_ENTRIES, "FWHM");
    expect(found.map((entry) => entry.id)).toEqual([
      "fwhm",
      "preset-recomendado",
    ]);
  });

  it("links every entry from a HelpHint and only to real entries", () => {
    const linked = linkedGlossaryIds();
    const known = new Set(GLOSSARY_ENTRIES.map((entry) => entry.id));
    const missing = GLOSSARY_ENTRIES.map((entry) => entry.id)
      .filter((id) => !linked.has(id))
      .sort();
    const unknown = [...linked].filter((id) => !known.has(id)).sort();

    expect(missing).toEqual([]);
    expect(unknown).toEqual([]);
  });

  it("narrows to the entries mentioning the text", () => {
    const found = filterGlossaryEntries(GLOSSARY_ENTRIES, "mucho ruido");
    expect(found.length).toBeGreaterThan(0);
    expect(found.length).toBeLessThan(GLOSSARY_ENTRIES.length);
  });
});
