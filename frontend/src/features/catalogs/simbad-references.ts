import type { SimbadObjectSchema } from "@/api/generated/model";

export type SimbadSourceRef = {
  sourceId: number;
  objectType: "point" | "extended";
};

export function simbadMatchedIds(
  objects: SimbadObjectSchema[],
  objectType: "point" | "extended",
): Set<number> {
  const ids = new Set<number>();
  for (const obj of objects) {
    const match = obj.image_match;
    if (!match?.matched) {
      continue;
    }
    if (String(match.object_type) !== objectType) {
      continue;
    }
    ids.add(match.source_id);
  }
  return ids;
}

export function simbadObjectsForSource(
  objects: SimbadObjectSchema[],
  sourceId: number,
  objectType: "point" | "extended",
): SimbadObjectSchema[] {
  return objects.filter((obj) => {
    const match = obj.image_match;
    if (!match?.matched) {
      return false;
    }
    if (match.source_id !== sourceId) {
      return false;
    }
    if (String(match.object_type) !== objectType) {
      return false;
    }
    return true;
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
  objects: SimbadObjectSchema[],
  pointIds: Set<number>,
  extendedIds: Set<number>,
): SimbadObjectSchema[] {
  return objects.filter((obj) => {
    const match = obj.image_match;
    if (!match?.matched) {
      return false;
    }
    const objectType = String(match.object_type);
    if (objectType === "point") {
      return pointIds.has(match.source_id);
    }
    if (objectType === "extended") {
      return extendedIds.has(match.source_id);
    }
    return false;
  });
}
