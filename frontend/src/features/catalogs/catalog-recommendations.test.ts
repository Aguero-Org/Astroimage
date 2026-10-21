import { describe, expect, it } from "vitest";
import type {
  CatalogJobStatusSchema,
  CatalogRecommendationItemSchema,
  CatalogRecommendationResponse,
} from "@/api/generated/model";
import { mockCatalogRecommendation } from "@/mocks/data/catalogs";
import {
  adsUrlForBibcode,
  type CatalogPublication,
  catalogueCrossmatchNote,
  catalogueMatchLabel,
  catalogueName,
  catalogueReason,
  catalogueSeparation,
  collectPublications,
  doiUrlFor,
  filterCatalogues,
  filterPublications,
  isCatalogJobStatus,
  isCatalogRecommendation,
  publicationLabel,
  regionDescription,
  shortenText,
  trimmedOrUndefined,
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
  it("distinguishes pending jobs from completed recommendations", () => {
    const pending = { status: "pending" } as unknown as CatalogJobStatusSchema;
    const completed = mockCatalogRecommendation();

    expect(isCatalogJobStatus(pending)).toBe(true);
    expect(isCatalogRecommendation(pending)).toBe(false);
    expect(isCatalogJobStatus(completed)).toBe(false);
    expect(isCatalogRecommendation(completed)).toBe(true);
    expect(isCatalogJobStatus(undefined)).toBe(false);
    expect(isCatalogRecommendation(undefined)).toBe(false);
  });

  it("falls back to the catalogue id when there is no title", () => {
    expect(catalogueName(item({ catalogue_title: "   " }))).toBe("X/1");
    expect(catalogueName(item({ catalogue_title: undefined }))).toBe("X/1");
    expect(catalogueName(item({ catalogue_title: " Gaia " }))).toBe("Gaia");
  });

  it("labels identifier and region matches", () => {
    expect(catalogueMatchLabel(item({ match_type: "OBJECT_IN_TABLE" }))).toBe(
      "Objeto identificado en el catálogo",
    );
    expect(catalogueMatchLabel(item({ match_type: "CATALOGUE_ONLY" }))).toBe(
      "Catálogo de la región",
    );
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
    expect(identifier.detail).toContain("columnas Name");

    const anonymousIdentifier = catalogueReason(
      item({ identifier_match: true, identifier_columns: "  " }),
    );
    expect(anonymousIdentifier.detail).toBe(
      "El identificador buscado aparece en este catálogo.",
    );

    expect(catalogueReason(item({ identifier_match: true })).detail).toBe(
      "El identificador buscado aparece en este catálogo.",
    );

    expect(
      catalogueReason(
        item({
          identifier_match: true,
          object_identifier: "M31",
          identifier_columns: "  Name  ",
        }),
      ).detail,
    ).toBe("El identificador M31 aparece en este catálogo (columnas Name).");

    expect(
      catalogueReason(
        item({
          identifier_match: true,
          object_identifier: "M31",
          identifier_columns: "   ",
        }),
      ).detail,
    ).toBe("El identificador M31 aparece en este catálogo.");

    const region = catalogueReason(
      item({ spatial_match: true, separation_arcsec: 12.3 }),
    );
    expect(region.headline).toMatch(/región del cielo/i);
    expect(region.detail).toContain("12.3″");

    const withoutSeparation = catalogueReason(
      item({ spatial_match: true, separation_arcsec: null }),
    );
    expect(withoutSeparation.detail).toBeUndefined();
    expect(
      catalogueReason(item({ spatial_match: true })).detail,
    ).toBeUndefined();
  });

  it("formats the queried region only for completed responses", () => {
    const completed = mockCatalogRecommendation();
    expect(regionDescription(completed)).toBe(
      "RA 10.6847° · Dec 41.2691° · radio 60.0″",
    );
    expect(
      regionDescription({
        ...completed,
        radius_arcsec: undefined,
      } as CatalogRecommendationResponse),
    ).toBeUndefined();
    expect(
      regionDescription({
        ...completed,
        dec_deg: null,
      } as CatalogRecommendationResponse),
    ).toBeUndefined();
    expect(
      regionDescription({
        ...completed,
        ra_deg: null,
      } as CatalogRecommendationResponse),
    ).toBeUndefined();
    expect(
      regionDescription({
        ...completed,
        ra_deg: undefined,
      } as CatalogRecommendationResponse),
    ).toBeUndefined();
    expect(
      regionDescription({
        ...completed,
        dec_deg: undefined,
      } as CatalogRecommendationResponse),
    ).toBeUndefined();
    expect(
      regionDescription({
        ...completed,
        status: "pending",
      } as unknown as CatalogRecommendationResponse),
    ).toBeUndefined();
  });

  it("formats separations and crossmatch counts", () => {
    expect(catalogueSeparation(item({ separation_arcsec: 0.346 }))).toBe(
      "0.35″",
    );
    expect(catalogueSeparation(item({ separation_arcsec: 12.3 }))).toBe(
      "12.3″",
    );
    expect(catalogueSeparation(item({ separation_arcsec: 1 }))).toBe("1.0″");
    expect(catalogueSeparation(item({ separation_arcsec: null }))).toBe(
      undefined,
    );
    expect(catalogueSeparation(item({}))).toBeUndefined();
    expect(catalogueCrossmatchNote(item({}))).toBeUndefined();
    expect(
      catalogueCrossmatchNote(
        item({
          crossmatch: {
            catalogue_id: "X/1",
            match_radius_arcsec: 2,
            matched_count: 2,
            detection_count: 5,
          },
        }),
      ),
    ).toBe("2 de 5 detecciones coinciden");
    expect(
      catalogueCrossmatchNote(
        item({
          crossmatch: { catalogue_id: "X/1", match_radius_arcsec: 2 },
        }),
      ),
    ).toBe("0 de 0 detecciones coinciden");
  });

  it("trims optional strings and labels publications", () => {
    expect(trimmedOrUndefined("  value ")).toBe("value");
    expect(trimmedOrUndefined("   ")).toBeUndefined();
    expect(trimmedOrUndefined(null)).toBeUndefined();
    expect(
      publicationLabel({
        id: "bibcode:B",
        bibcode: "B",
        doi: "D",
        kind: "catalogue-paper",
        catalogueIds: ["X/1"],
        catalogueNames: ["X"],
      } satisfies CatalogPublication),
    ).toBe("B");
    expect(
      publicationLabel({
        id: "doi:D",
        doi: "D",
        kind: "readme-reference",
        catalogueIds: ["X/1"],
        catalogueNames: ["X"],
      } satisfies CatalogPublication),
    ).toBe("D");
    expect(
      publicationLabel({
        id: "doi:",
        kind: "readme-reference",
        catalogueIds: ["X/1"],
        catalogueNames: ["X"],
      } satisfies CatalogPublication),
    ).toBe("Publicación");
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
    expect(
      filterCatalogues(items, { query: "  2mass  ", match: "all" }),
    ).toHaveLength(1);
    expect(
      filterCatalogues(
        [item({ catalogue_title: "Alpha", catalogue_id: "Beta" })],
        { query: "abet", match: "all" },
      ),
    ).toHaveLength(0);
    expect(
      filterCatalogues(items, { query: "Stryker", match: "all" }),
    ).toHaveLength(0);
    expect(
      filterCatalogues([item({ catalogue_title: "Alpha" })], {
        query: "Stryker",
        match: "all",
      }),
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
    expect(filterPublications(publications, "  2mass  ", "all")).toHaveLength(
      1,
    );
    expect(filterPublications(publications, "2021a&a", "all")).toHaveLength(1);
    expect(filterPublications(publications, "Stryker", "all")).toHaveLength(0);
    expect(
      filterPublications(
        [
          {
            id: "bibcode:B",
            bibcode: "B",
            kind: "catalogue-paper",
            catalogueIds: ["X/1"],
            catalogueNames: ["C"],
          },
        ],
        "bc",
      ),
    ).toHaveLength(0);
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
    expect(doiUrlFor("http://dx.doi.org/10.1/abc")).toBe(
      "https://doi.org/10.1%2Fabc",
    );
    expect(doiUrlFor(" 10.1/abc ")).toBe("https://doi.org/10.1%2Fabc");
    expect(doiUrlFor("prefix https://doi.org/10.1/abc")).toBe(
      "https://doi.org/prefix%20https%3A%2F%2Fdoi.org%2F10.1%2Fabc",
    );
  });

  it("merges papers that share a bibcode and ignores blank ReadMe entries", () => {
    const publications = collectPublications([
      item({
        catalogue_id: "A/1",
        catalogue_title: "Alpha",
        paper_bibcode: "2020A&A...1A...1A",
      }),
      item({
        catalogue_id: "B/2",
        catalogue_title: "Beta",
        paper_bibcode: "2020A&A...1A...1A",
        readme_bibcodes: ["  "],
        readme_dois: ["10.1/beta"],
      }),
    ]);

    expect(publications).toHaveLength(2);
    expect(publications[0]?.catalogueIds).toEqual(["A/1", "B/2"]);
    expect(publications[0]?.catalogueNames).toEqual(["Alpha", "Beta"]);
    expect(publications[1]).toMatchObject({
      doi: "10.1/beta",
      doiUrl: "https://doi.org/10.1%2Fbeta",
      kind: "readme-reference",
      catalogueIds: ["B/2"],
    });
  });

  it("keeps explicit paper URLs and ReadMe catalogue metadata", () => {
    const explicit = collectPublications([
      item({
        catalogue_id: "A/1",
        catalogue_title: "Alpha",
        paper_doi: "10.1/paper",
        paper_doi_url: "https://example.org/paper",
      }),
    ]);
    expect(explicit[0]).toMatchObject({
      doi: "10.1/paper",
      doiUrl: "https://example.org/paper",
      catalogueIds: ["A/1"],
      catalogueNames: ["Alpha"],
    });

    const readme = collectPublications([
      item({
        catalogue_id: "R/1",
        catalogue_title: "Readme",
        readme_bibcodes: [" B "],
        readme_dois: [" 10.1/r ", "10.1/s", "   "],
      }),
    ]);
    expect(readme).toHaveLength(3);
    expect(readme[0]).toMatchObject({
      id: "bibcode:B",
      bibcode: "B",
      catalogueIds: ["R/1"],
      catalogueNames: ["Readme"],
    });
    expect(readme[1]).toMatchObject({
      id: "doi:10.1/r",
      doi: "10.1/r",
      doiUrl: "https://doi.org/10.1%2Fr",
      catalogueIds: ["R/1"],
      catalogueNames: ["Readme"],
    });
    expect(readme[2]).toMatchObject({ id: "doi:10.1/s", doi: "10.1/s" });
  });

  it("searches authors and object identifiers as well as names", () => {
    const items = mockCatalogRecommendation().recommendations ?? [];

    expect(
      filterCatalogues(items, { query: "Cutri", match: "all" }),
    ).toHaveLength(1);
    expect(
      filterCatalogues(items, { query: "M31", match: "object" }),
    ).toHaveLength(1);
    expect(
      filterCatalogues(items, { query: "M31", match: "catalogue" }),
    ).toHaveLength(0);
  });

  it("searches publication DOIs and catalogue ids", () => {
    const publications = collectPublications(
      mockCatalogRecommendation().recommendations ?? [],
    );

    expect(filterPublications(publications, "10.26131/irsa1")).toHaveLength(1);
    expect(filterPublications(publications, "ii/246")).toHaveLength(1);
    expect(filterPublications(publications, "missing")).toHaveLength(0);
  });

  it("keeps text at the limit and truncates long words", () => {
    expect(shortenText("12345", 5)).toBe("12345");
    expect(shortenText("abcdefghij", 4)).toBe("abcd…");
    expect(shortenText("uno dos tres", 8)).toBe("uno dos…");
    expect(shortenText("uno  dos tres", 8)).toBe("uno…");
  });
});
