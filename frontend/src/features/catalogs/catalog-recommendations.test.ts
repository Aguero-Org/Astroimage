import { describe, expect, it } from "vitest";
import type { CatalogRecommendationItemSchema } from "@/api/generated/model";
import { mockCatalogRecommendation } from "@/mocks/data/catalogs";
import {
  adsUrlForBibcode,
  catalogueName,
  catalogueReason,
  collectPublications,
  doiUrlFor,
  filterCatalogues,
  filterPublications,
  shortenText,
} from "./catalog-recommendations";

function item(
  overrides: Partial<CatalogRecommendationItemSchema>,
): CatalogRecommendationItemSchema {
  return {
    rank: 1,
    catalogue_id: "X/1",
    match_type: "CATALOGUE_ONLY",
    ...overrides,
  };
}

describe("catalog-recommendations", () => {
  it("falls back to the catalogue id when there is no title", () => {
    expect(catalogueName(item({ catalogue_title: "   " }))).toBe("X/1");
    expect(catalogueName(item({ catalogue_title: "Gaia" }))).toBe("Gaia");
  });

  it("explains identifier matches and region coverage differently", () => {
    const identifier = catalogueReason(
      item({
        identifier_match: true,
        object_identifier: "M31",
        identifier_columns: "Name",
      }),
    );
    expect(identifier.headline).toMatch(/objeto buscado/i);
    expect(identifier.detail).toContain("M31");

    const region = catalogueReason(
      item({ spatial_match: true, separation_arcsec: 12.3 }),
    );
    expect(region.headline).toMatch(/región del cielo/i);
    expect(region.detail).toContain("12.3″");
  });

  it("deduplicates publications that share a bibcode across the paper and ReadMe", () => {
    const publications = collectPublications(
      mockCatalogRecommendation().recommendations ?? [],
    );

    expect(publications).toHaveLength(3);
    expect(
      publications.filter((p) => p.bibcode === "2021A&A...649A...1G"),
    ).toHaveLength(1);
    const found = publications.find((p) => p.kind === "catalogue-paper");
    expect(found?.bibcode).toBe("2021A&A...649A...1G");
    expect(found?.adsUrl).toBe(
      "https://ui.adsabs.harvard.edu/abs/2021A%26A...649A...1G/abstract",
    );
    expect(publications.filter((p) => p.doi === "10.26131/IRSA1")).toHaveLength(
      1,
    );
  });

  it("filters catalogues by query and match type", () => {
    const items = mockCatalogRecommendation().recommendations ?? [];
    expect(
      filterCatalogues(items, { query: "", match: "object" }),
    ).toHaveLength(1);
    expect(
      filterCatalogues(items, { query: "", match: "catalogue" }),
    ).toHaveLength(3);
    expect(
      filterCatalogues(items, { query: "2mass", match: "all" }),
    ).toHaveLength(1);
    expect(
      filterCatalogues(items, { query: "nope", match: "all" }),
    ).toHaveLength(0);
  });

  it("filters publications by kind and query", () => {
    const publications = collectPublications(
      mockCatalogRecommendation().recommendations ?? [],
    );
    expect(filterPublications(publications, "", "all")).toHaveLength(3);
    expect(
      filterPublications(publications, "", "catalogue-paper"),
    ).toHaveLength(1);
    expect(
      filterPublications(publications, "", "readme-reference"),
    ).toHaveLength(2);
    expect(filterPublications(publications, "2mass", "all")).toHaveLength(1);
  });

  it("keeps short text and truncates long text at a word boundary", () => {
    expect(shortenText("short text", 40)).toBe("short text");
    expect(shortenText("uno dos tres cuatro cinco seis", 12)).toBe("uno dos…");
    expect(shortenText("   ", 10)).toBeUndefined();
  });

  it("builds ADS and DOI links from raw identifiers", () => {
    expect(adsUrlForBibcode(" 2021A&A...649A...1G ")).toBe(
      "https://ui.adsabs.harvard.edu/abs/2021A%26A...649A...1G/abstract",
    );
    expect(doiUrlFor("https://doi.org/10.1/abc")).toBe(
      "https://doi.org/10.1%2Fabc",
    );
  });
});
