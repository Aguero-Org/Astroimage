import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MOCK_EXTENDED_SOURCE } from "@/mocks/data/image";
import { ExtendedSourceMarkers } from "./extended-source-markers";

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

describe("ExtendedSourceMarkers", () => {
  it("renders a rectangle sized from the region box", () => {
    render(<ExtendedSourceMarkers sources={[MOCK_EXTENDED_SOURCE]} />);

    const marker = screen.getByTestId("extended-source-marker");
    expect(marker).toBeInTheDocument();
    expect(marker).toHaveAttribute(
      "aria-label",
      "Fuente extendida 1, área 640 px",
    );

    const box = screen.getByTestId("extended-source-overlay")
      .firstChild as HTMLElement;
    expect(box).toBeInstanceOf(HTMLElement);
    expect(box as HTMLElement).toHaveStyle({
      left: "8px",
      top: "8px",
      width: "24px",
      height: "16px",
    });
  });

  it("returns null when there are no sources", () => {
    const { container } = render(<ExtendedSourceMarkers sources={[]} />);

    expect(container.firstChild).toBeNull();
  });
});
