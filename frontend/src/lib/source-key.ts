export type SourceKind = "point" | "extended";

export function sourceKey(kind: SourceKind, sourceId: number): string {
  return `${kind}:${sourceId}`;
}
