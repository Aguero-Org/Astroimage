import { QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { MOCK_POINT_SOURCE } from "@/mocks/data/image";
import { routeTree } from "@/routeTree.gen";
import { createTestQueryClient } from "@/test/render";

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

function renderImageDetail(recordId: string) {
  const queryClient = createTestQueryClient();
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({
      initialEntries: [`/image/${recordId}`],
    }),
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

describe("ImageDetailPage", () => {
  it("loads point markers without submitting the detection form", async () => {
    renderImageDetail("m31");

    const markerName = `Fuente ${MOCK_POINT_SOURCE.rank}, SNR ${MOCK_POINT_SOURCE.snr.toFixed(1)}`;

    await waitFor(
      () => {
        expect(screen.queryByTestId("render-loading")).not.toBeInTheDocument();
      },
      { timeout: 8000 },
    );
    await waitFor(
      () => {
        expect(screen.getByTestId("image-detail-title")).toBeInTheDocument();
        expect(screen.getByTestId("fits-viewer")).toBeInTheDocument();
        expect(screen.getByTestId("inspector-toggle")).toBeInTheDocument();
        expect(screen.getByTestId("source-detection-form")).toBeInTheDocument();
        expect(screen.getByTestId("source-marker")).toHaveAttribute(
          "aria-label",
          markerName,
        );
      },
      { timeout: 8000 },
    );
  });

  it("opens the inspector drawer from the hamburger control", async () => {
    const user = userEvent.setup();
    renderImageDetail("m31");

    await waitFor(() => {
      expect(screen.getByTestId("inspector-toggle")).toBeInTheDocument();
    });
    expect(screen.getByTestId("inspector-drawer")).not.toBeVisible();
    await user.click(screen.getByTestId("inspector-toggle"));
    expect(screen.getByTestId("inspector-drawer")).toBeVisible();
    expect(screen.getByTestId("inspector-section-sources")).toBeInTheDocument();
    expect(screen.getByTestId("hdu-selector")).toBeInTheDocument();
    await user.click(screen.getByTestId("inspector-section-view-toggle"));
    expect(screen.getByTestId("pixel-histogram")).toBeInTheDocument();
    await user.click(screen.getByTestId("inspector-section-archive-toggle"));
    expect(screen.getByTestId("meta-telescope")).toHaveTextContent("HST");
  });

  it("fills Selección when a point marker is clicked", async () => {
    const user = userEvent.setup();
    renderImageDetail("m31");

    await waitFor(
      () => {
        expect(screen.getByTestId("source-marker")).toBeInTheDocument();
      },
      { timeout: 8000 },
    );
    await user.click(screen.getByTestId("source-marker"));
    expect(screen.getByTestId("inspector-drawer")).toBeVisible();
    expect(screen.getByTestId("meta-sel-snr")).toHaveTextContent("11.20");
  });

  it("searches from the navbar and shows filtered home results", async () => {
    const user = userEvent.setup();
    renderImageDetail("m31");

    await waitFor(() => {
      expect(screen.getByTestId("search-input")).toBeInTheDocument();
    });

    await user.type(screen.getByTestId("search-input"), "orion");
    await user.click(screen.getByTestId("search-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("image-list")).toHaveTextContent(
        "M42 - Orion Nebula",
      );
    });
    expect(screen.getByTestId("image-list")).not.toHaveTextContent(
      "M31 - Andromeda Galaxy",
    );
  });
});
