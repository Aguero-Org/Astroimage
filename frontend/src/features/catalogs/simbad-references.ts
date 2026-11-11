import type { SimbadObjectSchema } from "@/api/generated/model";

export type SimbadSourceRef = {
  sourceId: number;
  objectType: "point" | "extended";
};

function matchedImage(obj: SimbadObjectSchema) {
  const match = obj.image_match;
  if (!match?.matched) {
    return undefined;
  }
  return match;
}

export function simbadMatchedIds(
  objects: readonly SimbadObjectSchema[],
  objectType: "point" | "extended",
): Set<number> {
  return new Set(
    objects.flatMap((obj) => {
      const match = matchedImage(obj);
      if (!match || String(match.object_type) !== objectType) {
        return [];
      }
      return [match.source_id];
    }),
  );
}

export function simbadObjectsForSource(
  objects: readonly SimbadObjectSchema[],
  sourceId: number,
  objectType: "point" | "extended",
): SimbadObjectSchema[] {
  return objects.filter((obj) => {
    const match = matchedImage(obj);
    return (
      match?.source_id === sourceId && String(match.object_type) === objectType
    );
  });
}

export function simbadSourceForObject(
  objects: SimbadObjectSchema[],
  mainId: string,
): SimbadSourceRef | undefined {
  const obj = objects.find((item) => item.main_id === mainId);
  const match = obj?.image_match;
  if (!match?.matched) {
    return undefined;
  }
  const objectType = String(match.object_type);
  if (objectType !== "point" && objectType !== "extended") {
    return undefined;
  }
  return { sourceId: match.source_id, objectType };
}

export function simbadObjectsInView(
  objects: readonly SimbadObjectSchema[],
  pointIds: ReadonlySet<number>,
  extendedIds: ReadonlySet<number>,
): SimbadObjectSchema[] {
  const idsByType = { point: pointIds, extended: extendedIds };
  return objects.filter((obj) => {
    const match = matchedImage(obj);
    if (!match) {
      return false;
    }
    const objectType = String(match.object_type);
    if (objectType !== "point" && objectType !== "extended") {
      return false;
    }
    return idsByType[objectType].has(match.source_id);
  });
}
