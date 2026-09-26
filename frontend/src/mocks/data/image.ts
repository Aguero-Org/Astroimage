import type {
  ExtendedSourceSchema,
  PointSourceSchema,
  SourceDetectionResponse,
} from "@/api/generated/model";

export type MockImageRecord = {
  record_id: string;
  slug: string;
  name: string;
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
  },
  {
    record_id: "m42",
    slug: "hst_m42.fits",
    name: "M42 - Orion Nebula",
  },
  {
    record_id: "ngc6992",
    slug: "hst_ngc6992.fits",
    name: "NGC 6992 - Veil Nebula",
  },
  {
    record_id: "ic1396",
    slug: "hst_ic1396.fits",
    name: "IC 1396 - Elephant Trunk Nebula",
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
    record.name.toLowerCase().includes(normalized),
  );
}
