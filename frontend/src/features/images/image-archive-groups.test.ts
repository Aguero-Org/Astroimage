import { describe, expect, it } from "vitest";
import type { FitsMetadataSchema } from "@/api/generated/model";
import { archiveGroupRows, IMAGE_ARCHIVE_GROUPS } from "./image-archive-groups";

const SAMPLE: FitsMetadataSchema = {
  source_name: "M31",
  instrument: { telescope: "HST", instrument: "WFC3" },
  image: { shape: [512, 512] },
  wcs: { present: true },
  hdus: {
    selected: 0,
    image_indices: [0],
    images: [{ index: 0, extname: "SCI" }],
  },
  header: { SIMPLE: true },
};

describe("IMAGE_ARCHIVE_GROUPS", () => {
  it("reads instrument and image fields from FitsMetadataSchema", () => {
    const instrument = IMAGE_ARCHIVE_GROUPS.find(
      (group) => group.testId === "archive-instrument",
    );
    const image = IMAGE_ARCHIVE_GROUPS.find(
      (group) => group.testId === "archive-image",
    );
    expect(instrument).toBeDefined();
    expect(image).toBeDefined();
    if (!instrument || !image) {
      return;
    }
    const instrumentRows = archiveGroupRows(instrument, SAMPLE);
    const imageRows = archiveGroupRows(image, SAMPLE);
    expect(instrumentRows.map((row) => row.id)).toEqual([
      "telescope",
      "instrument",
    ]);
    expect(imageRows[0]).toMatchObject({ id: "shape", value: "512 × 512" });
  });
});
