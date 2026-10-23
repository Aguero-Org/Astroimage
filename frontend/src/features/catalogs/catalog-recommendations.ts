import type {
  CatalogJobStatusSchema,
  CatalogPaperSchema,
  CatalogRecommendationItemSchema,
  CatalogRecommendationResponse,
} from "@/api/generated/model";

export type CatalogRecommendationBody =
  | CatalogRecommendationResponse
  | CatalogJobStatusSchema;

export type CatalogueMatchFilter = "all" | "object" | "catalogue";

export type PublicationKindFilter =
  | "all"
  | "catalogue-paper"
  | "readme-reference";

export type CatalogueReason = {
  headline: string;
  detail?: string;
};

export type CatalogPublication = {
  id: string;
  bibcode?: string;
  doi?: string;
  doiUrl?: string;
  adsUrl?: string;
  kind: "catalogue-paper" | "readme-reference";
  catalogueIds: string[];
  catalogueNames: string[];
  title?: string;
  abstract?: string;
};

export function isCatalogJobStatus(
  value: CatalogRecommendationBody | undefined,
): value is CatalogJobStatusSchema {
  return value?.status === "pending";
}

export function isCatalogRecommendation(
  value: CatalogRecommendationBody | undefined,
): value is CatalogRecommendationResponse {
  return value?.status === "completed";
}

export function catalogueName(item: CatalogRecommendationItemSchema): string {
  const title = item.catalogue_title?.trim();
  return title && title.length > 0 ? title : item.catalogue_id;
}

export function catalogueMatchLabel(
  item: CatalogRecommendationItemSchema,
): string {
  return item.match_type === "OBJECT_IN_TABLE"
    ? "Objeto identificado en el catálogo"
    : "Catálogo de la región";
}

export function catalogueReason(
  item: CatalogRecommendationItemSchema,
): CatalogueReason {
  if (item.identifier_match) {
    const columns = item.identifier_columns?.trim();
    const columnsNote = columns ? ` (columnas ${columns})` : "";
    const detail = item.object_identifier
      ? `El identificador ${item.object_identifier} aparece en este catálogo${columnsNote}.`
      : "El identificador buscado aparece en este catálogo.";
    return {
      headline: "El objeto buscado aparece en este catálogo",
      detail: detail.length > 0 ? detail : undefined,
    };
  }
  const separation = item.separation_arcsec;
  const detail =
    item.spatial_match && separation !== null && separation !== undefined
      ? `El centro de la región consultada cae a ${formatArcsec(separation)} de este catálogo.`
      : undefined;
  return { headline: "El catálogo cubre esta región del cielo", detail };
}

export function regionDescription(
  response: CatalogRecommendationBody | undefined,
): string | undefined {
  if (!isCatalogRecommendation(response)) {
    return undefined;
  }
  const { ra_deg: ra, dec_deg: dec, radius_arcsec: radius } = response;
  if (
    ra === null ||
    ra === undefined ||
    dec === null ||
    dec === undefined ||
    radius === undefined
  ) {
    return undefined;
  }
  return `RA ${formatDegrees(ra)} · Dec ${formatDegrees(dec)} · radio ${formatArcsec(radius)}`;
}

function formatDegrees(value: number): string {
  return `${value.toFixed(4)}°`;
}

export function catalogueSeparation(
  item: CatalogRecommendationItemSchema,
): string | undefined {
  const separation = item.separation_arcsec;
  if (separation === null || separation === undefined) {
    return undefined;
  }
  return formatArcsec(separation);
}

export function catalogueCrossmatchNote(
  item: CatalogRecommendationItemSchema,
): string | undefined {
  const crossmatch = item.crossmatch;
  if (!crossmatch) {
    return undefined;
  }
  const matched = crossmatch.matched_count ?? 0;
  const detections = crossmatch.detection_count ?? 0;
  return `${matched} de ${detections} detecciones coinciden`;
}

export function collectPublications(
  items: readonly CatalogRecommendationItemSchema[],
  papers: readonly CatalogPaperSchema[] = [],
): CatalogPublication[] {
  const publications = new Map<string, CatalogPublication>();
  for (const item of items) {
    const name = catalogueName(item);
    addCataloguePaper(publications, item, name);
    addReadmeBibcodes(publications, item, name);
    addReadmeDois(publications, item, name);
  }
  return [...publications.values()].map((publication) =>
    withPaperDetails(publication, papers),
  );
}

function addPublication(
  publications: Map<string, CatalogPublication>,
  publication: CatalogPublication,
): void {
  const existing = publications.get(publication.id);
  if (!existing) {
    publications.set(publication.id, publication);
    return;
  }
  existing.catalogueIds = [
    ...new Set([...existing.catalogueIds, ...publication.catalogueIds]),
  ];
  existing.catalogueNames = [
    ...new Set([...existing.catalogueNames, ...publication.catalogueNames]),
  ];
}

function addCataloguePaper(
  publications: Map<string, CatalogPublication>,
  item: CatalogRecommendationItemSchema,
  name: string,
): void {
  const bibcode = trimmedOrUndefined(item.paper_bibcode);
  const doi = trimmedOrUndefined(item.paper_doi);
  if (!bibcode && !doi) {
    return;
  }
  addPublication(publications, {
    id: publicationKey(bibcode, doi),
    bibcode,
    doi,
    doiUrl:
      trimmedOrUndefined(item.paper_doi_url) ??
      (doi ? doiUrlFor(doi) : undefined),
    adsUrl:
      trimmedOrUndefined(item.paper_ads_url) ??
      (bibcode ? adsUrlForBibcode(bibcode) : undefined),
    kind: "catalogue-paper",
    catalogueIds: [item.catalogue_id],
    catalogueNames: [name],
  });
}

function addReadmeBibcodes(
  publications: Map<string, CatalogPublication>,
  item: CatalogRecommendationItemSchema,
  name: string,
): void {
  for (const raw of item.readme_bibcodes ?? []) {
    const readmeBibcode = raw.trim();
    if (readmeBibcode.length === 0) {
      continue;
    }
    addPublication(publications, {
      id: publicationKey(readmeBibcode, undefined),
      bibcode: readmeBibcode,
      adsUrl: adsUrlForBibcode(readmeBibcode),
      kind: "readme-reference",
      catalogueIds: [item.catalogue_id],
      catalogueNames: [name],
    });
  }
}

function addReadmeDois(
  publications: Map<string, CatalogPublication>,
  item: CatalogRecommendationItemSchema,
  name: string,
): void {
  for (const raw of item.readme_dois ?? []) {
    const readmeDoi = raw.trim();
    if (readmeDoi.length === 0) {
      continue;
    }
    addPublication(publications, {
      id: publicationKey(undefined, readmeDoi),
      doi: readmeDoi,
      doiUrl: doiUrlFor(readmeDoi),
      kind: "readme-reference",
      catalogueIds: [item.catalogue_id],
      catalogueNames: [name],
    });
  }
}

export function trimmedOrUndefined(
  value: string | null | undefined,
): string | undefined {
  const trimmed = value?.trim();
  if (!trimmed) {
    return undefined;
  }
  return trimmed;
}

export function publicationLabel(publication: CatalogPublication): string {
  return publication.bibcode ?? publication.doi ?? "Publicación";
}

export function publicationHeading(publication: CatalogPublication): string {
  const title = publication.title?.trim();
  if (title) {
    return title;
  }
  const names = publication.catalogueNames.filter((name) => name.trim());
  if (names.length === 0) {
    return publicationLabel(publication);
  }
  const relation =
    publication.kind === "catalogue-paper" ? "Artículo de" : "Citada por";
  return `${relation} ${names.join(", ")}`;
}

export function filterCatalogues(
  items: readonly CatalogRecommendationItemSchema[],
  options: { query: string; match: CatalogueMatchFilter },
): CatalogRecommendationItemSchema[] {
  const needle = options.query.trim().toLowerCase();
  return items.filter((item) => {
    if (options.match === "object" && !item.identifier_match) {
      return false;
    }
    if (options.match === "catalogue" && item.identifier_match) {
      return false;
    }
    if (needle.length === 0) {
      return true;
    }
    const haystack = [
      catalogueName(item),
      item.catalogue_id,
      item.catalogue_authors ?? "",
      item.object_identifier ?? "",
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(needle);
  });
}

export function filterPublications(
  publications: readonly CatalogPublication[],
  query: string,
  kind: PublicationKindFilter = "all",
): CatalogPublication[] {
  const needle = query.trim().toLowerCase();
  return publications.filter((publication) => {
    if (kind !== "all" && publication.kind !== kind) {
      return false;
    }
    if (needle.length === 0) {
      return true;
    }
    const haystack = [
      publication.title ?? "",
      publication.abstract ?? "",
      publication.bibcode ?? "",
      publication.doi ?? "",
      ...publication.catalogueNames,
      ...publication.catalogueIds,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(needle);
  });
}

export function shortenText(
  value: string | null | undefined,
  maxLength = 220,
): string | undefined {
  const text = value?.trim();
  if (!text) {
    return undefined;
  }
  if (text.length <= maxLength) {
    return text;
  }
  const slice = text.slice(0, maxLength);
  const boundary = slice.lastIndexOf(" ");
  const trimmed = (boundary > 0 ? slice.slice(0, boundary) : slice).trimEnd();
  return `${trimmed}…`;
}

export function adsUrlForBibcode(bibcode: string): string {
  return `https://ui.adsabs.harvard.edu/abs/${encodeURIComponent(bibcode.trim())}/abstract`;
}

function withPaperDetails(
  publication: CatalogPublication,
  papers: readonly CatalogPaperSchema[],
): CatalogPublication {
  const match = papers.find((paper) => paperMatches(publication, paper));
  if (!match) {
    return publication;
  }
  return {
    ...publication,
    title: trimmedOrUndefined(match.title),
    abstract: trimmedOrUndefined(match.abstract),
  };
}

function paperMatches(
  publication: CatalogPublication,
  paper: CatalogPaperSchema,
): boolean {
  const bibcode = trimmedOrUndefined(paper.bibcode);
  const doi = trimmedOrUndefined(paper.doi);
  if (publication.bibcode && bibcode && publication.bibcode === bibcode) {
    return true;
  }
  return Boolean(publication.doi && doi && publication.doi === doi);
}

function publicationKey(
  bibcode: string | undefined,
  doi: string | undefined,
): string {
  return bibcode ? `bibcode:${bibcode}` : `doi:${doi}`;
}

export function doiUrlFor(doi: string): string {
  const normalized = doi.trim().replace(/^https?:\/\/(dx\.)?doi\.org\//i, "");
  return `https://doi.org/${encodeURIComponent(normalized)}`;
}

function formatArcsec(value: number): string {
  const digits = value < 1 ? 2 : 1;
  return `${value.toFixed(digits)}″`;
}
