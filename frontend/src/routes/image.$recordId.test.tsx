import { QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
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

    await waitFor(() => {
      expect(screen.getByRole("img", { name: markerName })).toBeInTheDocument();
    });
  });
});
