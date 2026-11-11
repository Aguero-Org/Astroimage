import { describe, expect, it } from "vitest";
import type { SimbadObjectSchema } from "@/api/generated/model";
import { MOCK_SIMBAD_OBJECT } from "@/mocks/data/simbad";
import {
  simbadMatchedIds,
  simbadObjectsForSource,
  simbadObjectsInView,
  simbadSourceForObject,
} from "./simbad-references";

function withMatch(
  mainId: string,
  match: SimbadObjectSchema["image_match"],
): SimbadObjectSchema {
  return { ...MOCK_SIMBAD_OBJECT, main_id: mainId, image_match: match };
}

const point = withMatch("M  31", {
  source_id: 7,
  object_type: "point",
  separation_arcsec: 0.1,
  probability: 0.9,
  matched: true,
});
const extended = withMatch("* alf And", {
  source_id: 8,
  object_type: "extended",
  separation_arcsec: 1,
  probability: 0.5,
  matched: true,
});
const unmatched = withMatch("NGC 1", {
  source_id: 9,
  object_type: "point",
  separation_arcsec: 3,
  probability: 0,
  matched: false,
});
const unknown = withMatch("NGC 2", {
  source_id: 10,
  object_type: "other",
  separation_arcsec: 1,
  probability: 0.2,
  matched: true,
});
const bare = withMatch("bare", null);
const objects = [point, extended, unmatched, unknown, bare];

describe("simbad-references", () => {
  it("collects matched source ids of one object type", () => {
    expect(simbadMatchedIds(objects, "point")).toEqual(new Set([7]));
    expect(simbadMatchedIds(objects, "extended")).toEqual(new Set([8]));
  });

  it("returns the objects tied to one detection", () => {
    expect(simbadObjectsForSource(objects, 7, "point")).toEqual([point]);
    expect(simbadObjectsForSource(objects, 7, "extended")).toEqual([]);
    expect(simbadObjectsForSource(objects, 9, "point")).toEqual([]);
  });

  it("keeps objects whose detection is in view", () => {
    expect(simbadObjectsInView(objects, new Set([7]), new Set([8]))).toEqual([
      point,
      extended,
    ]);
    expect(simbadObjectsInView(objects, new Set(), new Set([8]))).toEqual([
      extended,
    ]);
  });

  it("resolves a source from the object name", () => {
    expect(simbadSourceForObject(objects, "M  31")).toEqual({
      sourceId: 7,
      objectType: "point",
    });
    expect(simbadSourceForObject(objects, "* alf And")).toEqual({
      sourceId: 8,
      objectType: "extended",
    });
    expect(simbadSourceForObject(objects, "NGC 1")).toBeUndefined();
    expect(simbadSourceForObject(objects, "NGC 2")).toBeUndefined();
    expect(simbadSourceForObject(objects, "missing")).toBeUndefined();
  });
});
