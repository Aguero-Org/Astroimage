import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SourceMarkers } from "./source-markers";

vi.mock("@cellbytes/react-openseadragon", () => ({
  useCoordinates: () => ({
    tiledImage: {},
    imageToViewport: (coordinateX: number, coordinateY: number) => ({
      x: coordinateX,
      y: coordinateY,
    }),
    viewportToPixel: (point: { x: number; y: number }) => point,
  }),
  useViewerEvent: vi.fn(),
}));

describe("SourceMarkers", () => {
  it("places a marker at image pixel coordinates", () => {
    render(
      <SourceMarkers
        sources={[
          {
            source_id: 7,
            rank: 2,
            xcentroid: 40,
            ycentroid: 15,
            snr: 9.4,
            relevance_score: 0.5,
            object_type: "point",
          },
        ]}
      />,
    );

    expect(
      screen.getByRole("img", { name: "Fuente 2, SNR 9.4" }),
    ).toBeInTheDocument();
  });

  it("marks an extended source over the image", () => {
    render(
      <SourceMarkers
        sources={[
          {
            source_id: 7,
            rank: 2,
            xcentroid: 40,
            ycentroid: 15,
            snr: 9.4,
            relevance_score: 0.5,
            object_type: "point",
          },
        ]}
        extendedSources={[
          {
            source_id: 101,
            rank: 1,
            xcentroid: 90.25,
            ycentroid: 55.5,
            snr: 5400,
            object_type: "extended",
          },
        ]}
      />,
    );

    expect(
      screen.getByRole("img", { name: "Extendida 1, SNR 5400.0" }),
    ).toBeInTheDocument();
  });
});
