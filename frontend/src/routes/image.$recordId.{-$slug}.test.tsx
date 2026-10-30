import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { MOCK_EXTENDED_SOURCE, MOCK_POINT_SOURCE } from "@/mocks/data/image";
import { simbadReferencesResponse } from "@/mocks/data/simbad";
import { renderWithRouter } from "@/test/router";
import { server } from "@/test/server";

vi.mock("@cellbytes/react-openseadragon", () => ({
  useOpenseadragon: () => ({
    setContainerElement: vi.fn(),
  }),
  ViewerStateProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  TiledImage: () => null,
  useViewer: () => ({ viewer: null }),
  useViewerEvent: vi.fn(),
  useCoordinates: () => ({
    tiledImage: {},
    imageToViewport: (coordinateX: number, coordinateY: number) => ({
      x: coordinateX,
      y: coordinateY,
    }),
    viewportToPixel: (point: { x: number; y: number }) => point,
  }),
}));

describe("ImageDetailPage", () => {
  it("loads point markers without submitting the detection form", async () => {
    renderWithRouter("/image/m31");

    const markerName = `Fuente ${MOCK_POINT_SOURCE.rank}, SNR ${MOCK_POINT_SOURCE.snr.toFixed(1)}`;
    const extendedName = `Fuente extendida ${MOCK_EXTENDED_SOURCE.rank}, área ${MOCK_EXTENDED_SOURCE.area_pixels} px`;

    await waitFor(
      () => {
        expect(screen.queryByTestId("render-loading")).not.toBeInTheDocument();
      },
      { timeout: 8000 },
    );
    await waitFor(
      () => {
        expect(screen.getByTestId("image-detail-title")).toBeInTheDocument();
        expect(document.title).toMatch(/ - Astroimage$/);
        expect(screen.getByTestId("fits-viewer")).toBeInTheDocument();
        expect(screen.getByTestId("inspector-toggle")).toBeInTheDocument();
        expect(screen.getByTestId("source-detection-form")).toBeInTheDocument();
        expect(screen.getByTestId("source-marker")).toHaveAttribute(
          "aria-label",
          markerName,
        );
        expect(screen.getByTestId("extended-source-marker")).toHaveAttribute(
          "aria-label",
          extendedName,
        );
      },
      { timeout: 8000 },
    );
  });

  it("opens the inspector drawer from the hamburger control", async () => {
    const user = userEvent.setup();
    renderWithRouter("/image/m31");

    await waitFor(
      () => {
        expect(screen.getByTestId("inspector-toggle")).toBeInTheDocument();
      },
      { timeout: 8000 },
    );
    expect(screen.getByTestId("inspector-drawer")).toHaveAttribute(
      "data-state",
      "collapsed",
    );
    await user.click(screen.getByTestId("inspector-toggle"));
    expect(screen.getByTestId("inspector-drawer")).toHaveAttribute(
      "data-state",
      "expanded",
    );
    expect(screen.getByTestId("inspector-section-sources")).toBeInTheDocument();
    expect(screen.getByTestId("hdu-selector")).toBeInTheDocument();
    await user.click(screen.getByTestId("inspector-section-view-toggle"));
    expect(screen.getByTestId("pixel-histogram")).toBeInTheDocument();
    await user.click(screen.getByTestId("inspector-section-archive-toggle"));
    expect(screen.getByTestId("meta-telescope")).toHaveTextContent("HST");
  });

  it("fills Selección when a point marker is clicked", async () => {
    const user = userEvent.setup();
    renderWithRouter("/image/m31");

    await waitFor(
      () => {
        expect(screen.getByTestId("source-marker")).toBeInTheDocument();
      },
      { timeout: 8000 },
    );
    await user.click(screen.getByTestId("source-marker"));
    expect(screen.getByTestId("inspector-drawer")).toHaveAttribute(
      "data-state",
      "expanded",
    );
    expect(screen.getByTestId("meta-sel-snr")).toHaveTextContent("11.20");
  });

  it("fills Selección when an extended marker is clicked", async () => {
    const user = userEvent.setup();
    renderWithRouter("/image/m31");

    await waitFor(
      () => {
        expect(
          screen.getByTestId("extended-source-marker"),
        ).toBeInTheDocument();
      },
      { timeout: 8000 },
    );
    await user.click(screen.getByTestId("extended-source-marker"));
    expect(screen.getByTestId("inspector-drawer")).toHaveAttribute(
      "data-state",
      "expanded",
    );
    expect(screen.getByTestId("extended-source-selection")).toBeInTheDocument();
    expect(screen.getByTestId("meta-sel-area")).toHaveTextContent("640 px²");
  });

  it("cross-matches with Gaia automatically and opens recommendations", async () => {
    renderWithRouter("/image/m31");

    await waitFor(
      () => {
        expect(screen.getByTestId("gaia-summary")).toHaveTextContent(
          "Puntuales 1/1",
        );
      },
      { timeout: 8000 },
    );
    expect(screen.getByTestId("scientific-workspace")).toBeInTheDocument();
    await waitFor(
      () => {
        expect(screen.getByTestId("catalog-list")).toBeInTheDocument();
      },
      { timeout: 8000 },
    );
  });

  it("requests SIMBAD once when the workspace opens", async () => {
    const onRequest = vi.fn();
    server.use(
      http.get(
        "http://localhost:8000/image/:recordId/simbad-references",
        () => {
          onRequest();
          return HttpResponse.json(simbadReferencesResponse);
        },
      ),
    );
    renderWithRouter("/image/m31");

    await waitFor(
      () => {
        expect(screen.getByTestId("scientific-tab-simbad")).toHaveTextContent(
          "SIMBAD (2)",
        );
      },
      { timeout: 8000 },
    );
    expect(onRequest).toHaveBeenCalledTimes(1);
  });

  it("shows the not-found view when the image info returns 404", async () => {
    server.use(
      http.get("http://localhost:8000/image/:recordId/info", () =>
        HttpResponse.json({ detail: "Image not found" }, { status: 404 }),
      ),
    );
    renderWithRouter("/image/missing");

    await waitFor(
      () => {
        expect(
          screen.getByRole("heading", { name: "Imagen no encontrada" }),
        ).toBeInTheDocument();
      },
      { timeout: 8000 },
    );
    expect(
      screen.getByRole("link", { name: "Volver al inicio" }),
    ).toHaveAttribute("href", "/");
  });

  it("searches from the navbar and shows filtered home results", async () => {
    const user = userEvent.setup();
    renderWithRouter("/image/m31");

    await waitFor(
      () => {
        expect(screen.getByTestId("search-input")).toBeInTheDocument();
      },
      { timeout: 8000 },
    );

    await user.type(screen.getByTestId("search-input"), "orion");
    await user.click(screen.getByTestId("search-submit"));

    await waitFor(
      () => {
        expect(screen.getByTestId("image-list")).toHaveTextContent(
          "M42 - Orion Nebula",
        );
      },
      { timeout: 8000 },
    );
    expect(screen.getByTestId("image-list")).not.toHaveTextContent(
      "M31 - Andromeda Galaxy",
    );
  });
});
