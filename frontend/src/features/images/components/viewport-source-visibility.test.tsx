import { render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type {
  ExtendedSourceSchema,
  PointSourceSchema,
} from "@/api/generated/model";
import { ViewportSourceVisibility } from "./viewport-source-visibility";

const viewerState = vi.hoisted(() => ({
  bounds: { x: 0, y: 0, width: 10, height: 10 },
}));

vi.mock("@cellbytes/react-openseadragon", () => ({
  useViewer: () => ({
    viewer: {
      viewport: {
        getBounds: () => viewerState.bounds,
      },
    },
  }),
  useCoordinates: () => ({
    tiledImage: {},
    imageToViewport: (x: number, y: number) => ({ x, y }),
  }),
  useViewerEvent: vi.fn(),
}));

function pointSource(
  sourceId: number,
  x: number,
  y: number,
): PointSourceSchema {
  return {
    source_id: sourceId,
    rank: sourceId,
    xcentroid: x,
    ycentroid: y,
    snr: 10,
    relevance_score: 0.5,
    object_type: "point",
  };
}

const EXTENDED_SOURCE: ExtendedSourceSchema = {
  source_id: 1,
  rank: 1,
  xcentroid: 8,
  ycentroid: 8,
  width_pixels: 4,
  height_pixels: 4,
  area_pixels: 16,
  relevance_score: 0.5,
  object_type: "extended",
  peak: 9,
  mean: 3,
  flux: 50,
};

describe("ViewportSourceVisibility", () => {
  it("reports only point and extended sources inside the viewport", async () => {
    const onVisibleSourceKeysChange = vi.fn();

    render(
      <ViewportSourceVisibility
        pointSources={[pointSource(1, 5, 5), pointSource(2, 15, 5)]}
        extendedSources={[EXTENDED_SOURCE]}
        onVisibleSourceKeysChange={onVisibleSourceKeysChange}
      />,
    );

    await waitFor(() => {
      expect(onVisibleSourceKeysChange).toHaveBeenCalledWith(
        new Set(["point:1", "extended:1"]),
      );
    });
  });
});
