import type {
  PointSourceSchema,
  SourceDetectionResponse,
} from "@/api/generated/model";

export type MockImageRecord = {
  record_id: string;
  name: string;
};

export const MOCK_POINT_SOURCE: PointSourceSchema = {
  source_id: 1,
  rank: 1,
  xcentroid: 12.5,
  ycentroid: 8.25,
  snr: 11.2,
  relevance_score: 0.64,
  object_type: "point",
};

export function mockSourceDetection(
  record: MockImageRecord,
): SourceDetectionResponse {
  return {
    source_name: record.name,
    summary: { point_count: 1, extended_count: 0 },
    point_sources: [MOCK_POINT_SOURCE],
    extended_sources: [],
  };
}

export const mockRecords: MockImageRecord[] = [
  { record_id: "m31", name: "M31 - Andromeda Galaxy" },
  { record_id: "m42", name: "M42 - Orion Nebula" },
  { record_id: "ngc6992", name: "NGC 6992 - Veil Nebula" },
  { record_id: "ic1396", name: "IC 1396 - Elephant Trunk Nebula" },
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
