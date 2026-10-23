import { render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { PointSourceSchema } from "@/api/generated/model";
import { ViewportFocusController } from "./viewport-focus-controller";

const viewerState = vi.hoisted(() => ({
  fitBounds: vi.fn(),
  imageToViewportRect: vi.fn(() => ({
    x: 0,
    y: 0,
    width: 1,
    height: 1,
  })),
}));

vi.mock("@cellbytes/react-openseadragon", () => ({
  useViewer: () => ({
    viewer: {
      viewport: {
        fitBounds: viewerState.fitBounds,
      },
    },
  }),
  useCoordinates: () => ({
    tiledImage: {
      getContentSize: () => ({ x: 100, y: 100 }),
    },
    imageToViewportRect: viewerState.imageToViewportRect,
  }),
}));

const POINT_SOURCE: PointSourceSchema = {
  source_id: 1,
  rank: 1,
  xcentroid: 50,
  ycentroid: 50,
  snr: 10,
  relevance_score: 0.5,
  object_type: "point",
};

describe("ViewportFocusController", () => {
  it("fits the viewport around the requested source", async () => {
    render(
      <ViewportFocusController
        request={{ requestId: 1, source: POINT_SOURCE }}
      />,
    );

    await waitFor(() => {
      expect(viewerState.imageToViewportRect).toHaveBeenCalledWith(
        38,
        38,
        24,
        24,
      );
      expect(viewerState.fitBounds).toHaveBeenCalledWith({
        x: 0,
        y: 0,
        width: 1,
        height: 1,
      });
    });
  });
});
