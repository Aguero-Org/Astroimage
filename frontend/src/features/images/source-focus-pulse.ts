export type SourceFocusPulse = {
  sourceId: number;
  objectType: "point" | "extended";
  nonce: number;
};

export function sourceFocusPulseKey(
  pulse: SourceFocusPulse | null | undefined,
  sourceId: number,
  objectType: "point" | "extended",
): number | undefined {
  if (pulse?.sourceId !== sourceId || pulse.objectType !== objectType) {
    return undefined;
  }
  return pulse.nonce;
}
