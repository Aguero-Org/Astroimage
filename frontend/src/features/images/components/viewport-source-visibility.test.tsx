import { useViewerEvent } from "@cellbytes/react-openseadragon";
import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  ExtendedSourceSchema,
  PointSourceSchema,
} from "@/api/generated/model";
import {
  ViewportSourceVisibility,
  visibleSourceKeys,
} from "./viewport-source-visibility";

type Bounds = { x: number; y: number; width: number; height: number };

const VIEW: Bounds = { x: 0, y: 0, width: 10, height: 10 };

const viewerState = vi.hoisted(() => ({
  bounds: { x: 0, y: 0, width: 10, height: 10 } as Bounds,
  viewer: null as {
    viewport: { getBounds: () => Bounds };
  } | null,
  tiledImage: null as object | null,
  handlers: [] as { name: string; handler: () => void }[],
}));

vi.mock("@cellbytes/react-openseadragon", () => ({
  useViewer: () => ({ viewer: viewerState.viewer }),
  useCoordinates: () => ({
    tiledImage: viewerState.tiledImage,
    imageToViewport: (x: number, y: number) => ({ x, y }),
  }),
  useViewerEvent: vi.fn((name: string, handler: () => void) => {
    viewerState.handlers.push({ name, handler });
  }),
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

function extendedSource(
  sourceId: number,
  x: number,
  y: number,
  width: number,
  height: number,
): ExtendedSourceSchema {
  return {
    source_id: sourceId,
    rank: sourceId,
    xcentroid: x,
    ycentroid: y,
    width_pixels: width,
    height_pixels: height,
    area_pixels: width * height,
    relevance_score: 0.5,
    object_type: "extended",
    peak: 9,
    mean: 3,
    flux: 50,
  };
}

const identity = (x: number, y: number) => ({ x, y });

function extendedKeys(sources: readonly ExtendedSourceSchema[]): string[] {
  return [...visibleSourceKeys([], sources, VIEW, identity)].sort();
}

describe("visibleSourceKeys", () => {
  it("keeps points on every viewport edge", () => {
    const points = [
      pointSource(1, 0, 5),
      pointSource(2, 10, 5),
      pointSource(3, 5, 0),
      pointSource(4, 5, 10),
      pointSource(5, -0.1, 5),
      pointSource(6, 10.1, 5),
      pointSource(7, 5, -0.1),
      pointSource(8, 5, 10.1),
    ];

    expect(visibleSourceKeys(points, [], VIEW, identity)).toEqual(
      new Set(["point:1", "point:2", "point:3", "point:4"]),
    );
  });

  it("keeps an extended box that touches an edge", () => {
    expect(
      extendedKeys([
        extendedSource(1, 12, 5, 4, 4),
        extendedSource(2, 12.2, 5, 4, 4),
        extendedSource(3, -2, 5, 4, 4),
        extendedSource(4, -2.2, 5, 4, 4),
        extendedSource(5, 5, 12, 4, 4),
        extendedSource(6, 5, 12.2, 4, 4),
        extendedSource(7, 5, -2, 4, 4),
        extendedSource(8, 5, -2.2, 4, 4),
        extendedSource(9, 30, 30, 2, 2),
      ]),
    ).toEqual(["extended:1", "extended:3", "extended:5", "extended:7"]);
  });

  it("drops a box that only reaches the viewport if it is grown", () => {
    expect(
      extendedKeys([
        extendedSource(1, 14, 5, 4, 2),
        extendedSource(2, 5, 14, 2, 4),
        extendedSource(3, -5, 5, 2, 2),
        extendedSource(4, 5, -5, 2, 2),
      ]),
    ).toEqual([]);
  });

  it("keeps a box that overlaps on one side of the centroid", () => {
    expect(
      extendedKeys([
        extendedSource(1, 11, 5, 4, 2),
        extendedSource(2, -1, 5, 6, 2),
        extendedSource(3, 5, 11, 2, 4),
        extendedSource(4, 5, -1, 2, 6),
        extendedSource(5, 9, 5, 4, 2),
        extendedSource(6, 5, 9, 2, 4),
      ]),
    ).toEqual([
      "extended:1",
      "extended:2",
      "extended:3",
      "extended:4",
      "extended:5",
      "extended:6",
    ]);
  });
});

describe("ViewportSourceVisibility", () => {
  beforeEach(() => {
    viewerState.bounds = { x: 0, y: 0, width: 10, height: 10 };
    viewerState.viewer = {
      viewport: { getBounds: () => viewerState.bounds },
    };
    viewerState.tiledImage = {};
    viewerState.handlers = [];
  });

  it("reports only point and extended sources inside the viewport", async () => {
    const onVisibleSourceKeysChange = vi.fn();

    render(
      <ViewportSourceVisibility
        pointSources={[pointSource(1, 5, 5), pointSource(2, 15, 5)]}
        extendedSources={[extendedSource(1, 8, 8, 4, 4)]}
        onVisibleSourceKeysChange={onVisibleSourceKeysChange}
      />,
    );

    await waitFor(() => {
      expect(onVisibleSourceKeysChange).toHaveBeenCalledWith(
        new Set(["point:1", "extended:1"]),
      );
    });
    expect(useViewerEvent).toHaveBeenCalledWith(
      "animation-finish",
      expect.any(Function),
    );
    expect(useViewerEvent).toHaveBeenCalledWith("resize", expect.any(Function));
  });

  it("does not notify when the viewer or the callback is missing", () => {
    const onVisibleSourceKeysChange = vi.fn();
    viewerState.viewer = null;

    render(
      <ViewportSourceVisibility
        pointSources={[pointSource(1, 5, 5)]}
        extendedSources={[]}
        onVisibleSourceKeysChange={onVisibleSourceKeysChange}
      />,
    );

    expect(onVisibleSourceKeysChange).not.toHaveBeenCalled();

    viewerState.viewer = {
      viewport: { getBounds: () => viewerState.bounds },
    };
    viewerState.tiledImage = null;

    render(
      <ViewportSourceVisibility
        pointSources={[pointSource(1, 5, 5)]}
        extendedSources={[]}
        onVisibleSourceKeysChange={onVisibleSourceKeysChange}
      />,
    );

    expect(onVisibleSourceKeysChange).not.toHaveBeenCalled();

    viewerState.tiledImage = {};
    render(
      <ViewportSourceVisibility
        pointSources={[pointSource(1, 5, 5)]}
        extendedSources={[]}
      />,
    );
  });

  it("notifies again only when the visible set changes", async () => {
    const onVisibleSourceKeysChange = vi.fn();
    const props = {
      pointSources: [pointSource(1, 5, 5)],
      extendedSources: [],
      onVisibleSourceKeysChange,
    };

    const view = render(<ViewportSourceVisibility {...props} />);

    await waitFor(() => {
      expect(onVisibleSourceKeysChange).toHaveBeenCalledTimes(1);
    });

    const finish = viewerState.handlers.findLast(
      (entry) => entry.name === "animation-finish",
    );
    finish?.handler();
    expect(onVisibleSourceKeysChange).toHaveBeenCalledTimes(1);

    view.rerender(
      <ViewportSourceVisibility
        {...props}
        pointSources={[pointSource(1, 15, 5)]}
      />,
    );

    await waitFor(() => {
      expect(onVisibleSourceKeysChange).toHaveBeenCalledTimes(2);
    });
    expect(onVisibleSourceKeysChange).toHaveBeenLastCalledWith(new Set());
  });

  it("keeps the same notice when the same points arrive in another order", async () => {
    const onVisibleSourceKeysChange = vi.fn();
    const view = render(
      <ViewportSourceVisibility
        pointSources={[pointSource(1, 5, 5), pointSource(2, 4, 5)]}
        extendedSources={[]}
        onVisibleSourceKeysChange={onVisibleSourceKeysChange}
      />,
    );

    await waitFor(() => {
      expect(onVisibleSourceKeysChange).toHaveBeenCalledTimes(1);
    });
    expect(onVisibleSourceKeysChange).toHaveBeenCalledWith(
      new Set(["point:1", "point:2"]),
    );

    view.rerender(
      <ViewportSourceVisibility
        pointSources={[pointSource(2, 4, 5), pointSource(1, 5, 5)]}
        extendedSources={[]}
        onVisibleSourceKeysChange={onVisibleSourceKeysChange}
      />,
    );

    expect(onVisibleSourceKeysChange).toHaveBeenCalledTimes(1);
  });
});
