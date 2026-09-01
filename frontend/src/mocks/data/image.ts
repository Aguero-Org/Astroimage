export type MockImageRecord = {
  record_id: string;
  name: string;
};

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
