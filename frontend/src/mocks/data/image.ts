import type {
  ExtendedSourceSchema,
  PointSourceSchema,
  SourceDetectionResponse,
} from "@/api/generated/model";

export type MockImageRecord = {
  record_id: string;
  slug: string;
  name: string;
  display_name: string;
  instrument: string | null;
  proposal_id: string;
  filters: string | null;
  observed_at: string | null;
  created_at: string;
  size_bytes: number;
  data_uri: string;
};

export const MOCK_POINT_SOURCE: PointSourceSchema = {
  source_id: 1,
  rank: 1,
  xcentroid: 12.5,
  ycentroid: 8.25,
  snr: 11.2,
  relevance_score: 0.64,
  peak: 42.1,
  flux: 128.4,
  object_type: "point",
};

export const MOCK_EXTENDED_SOURCE: ExtendedSourceSchema = {
  source_id: 1,
  rank: 1,
  xcentroid: 20,
  ycentroid: 16,
  width_pixels: 24,
  height_pixels: 16,
  area_pixels: 640,
  peak: 9.4,
  mean: 3.2,
  flux: 55.6,
  relevance_score: 0.72,
  object_type: "extended",
};

export function mockSourceDetection(
  record: MockImageRecord,
): SourceDetectionResponse {
  return {
    source_name: record.name,
    summary: { point_count: 1, extended_count: 1 },
    point_sources: [MOCK_POINT_SOURCE],
    extended_sources: [MOCK_EXTENDED_SOURCE],
  };
}

export const mockRecords: MockImageRecord[] = [
  {
    record_id: "m31",
    slug: "hst_m31.fits",
    name: "M31 - Andromeda Galaxy",
    display_name: "M31 - Andromeda Galaxy",
    observed_at: "2011-01-15",
    created_at: "2026-09-01T00:00:00Z",
    instrument: "WFC3",
    proposal_id: "12055",
    filters: "F606W",
    size_bytes: 120 * 1024 * 1024,
    data_uri: "mast:HST/product/hst_m31.fits",
  },
  {
    record_id: "m42",
    slug: "hst_m42.fits",
    name: "M42 - Orion Nebula",
    display_name: "M42 - Orion Nebula",
    observed_at: "2004-03-02",
    created_at: "2026-09-02T00:00:00Z",
    instrument: "ACS",
    proposal_id: "9822",
    filters: "F658N",
    size_bytes: 80 * 1024 * 1024,
    data_uri: "mast:HST/product/hst_m42.fits",
  },
  {
    record_id: "ngc6992",
    slug: "hst_ngc6992.fits",
    name: "NGC 6992 - Veil Nebula",
    display_name: "NGC 6992 - Veil Nebula",
    observed_at: "2013-08-20",
    created_at: "2026-09-03T00:00:00Z",
    instrument: "WFC3",
    proposal_id: "13456",
    filters: "F502N",
    size_bytes: 90 * 1024 * 1024,
    data_uri: "mast:HST/product/hst_ngc6992.fits",
  },
  {
    record_id: "ic1396",
    slug: "hst_ic1396.fits",
    name: "IC 1396 - Elephant Trunk Nebula",
    display_name: "IC 1396 - Elephant Trunk Nebula",
    observed_at: "2005-11-11",
    created_at: "2026-09-04T00:00:00Z",
    instrument: "ACS",
    proposal_id: "10246",
    filters: "F550M",
    size_bytes: 70 * 1024 * 1024,
    data_uri: "mast:HST/product/hst_ic1396.fits",
  },
];

export function findRecord(recordId: string): MockImageRecord | undefined {
  return mockRecords.find((record) => record.record_id === recordId);
}

export function filterRecords(
  cuerpoCeleste?: string | null,
): MockImageRecord[] {
  if (!cuerpoCeleste) {
    return mockRecords;
  }
  const normalized = cuerpoCeleste.toLowerCase().trim();
  if (normalized === "") {
    return mockRecords;
  }
  return mockRecords.filter((record) =>
    [
      record.display_name,
      record.name,
      record.instrument ?? "",
      record.proposal_id,
      record.data_uri,
    ].some((value) => value.toLowerCase().includes(normalized)),
  );
}
