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

    const marker = screen.getByTestId("source-marker");
    expect(marker).toBeInTheDocument();
    expect(marker).toHaveAttribute("aria-label", "Fuente 2, SNR 9.4");
    expect(marker).toHaveAttribute("data-gaia-match", "false");
    expect(marker).toHaveAttribute("data-simbad-match", "false");
    expect(screen.queryByTestId("simbad-match-badge")).not.toBeInTheDocument();
  });

  it("paints a Gaia counterpart green", () => {
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
        gaiaMatchedIds={new Set([7])}
      />,
    );

    expect(screen.getByTestId("source-marker")).toHaveAttribute(
      "data-gaia-match",
      "true",
    );
    expect(screen.getByTestId("source-marker")).toHaveClass("border-gaia");
  });

  it("marks a SIMBAD counterpart with a badge", () => {
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
        simbadMatchedIds={new Set([7])}
      />,
    );

    const marker = screen.getByTestId("source-marker");
    expect(marker).toHaveAttribute("data-simbad-match", "true");
    expect(marker).toHaveAttribute("aria-label", "Fuente 2, SNR 9.4, SIMBAD");
    expect(screen.getByTestId("simbad-match-badge")).toHaveClass("bg-simbad");
  });
});
