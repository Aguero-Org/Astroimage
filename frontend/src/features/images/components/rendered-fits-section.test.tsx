import { render, renderHook, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  RenderedFitsSection,
  type SourceOverlays,
  useRenderedObjectUrl,
} from "./rendered-fits-section";

vi.mock("@/features/images/components/fits-image-viewer", () => ({
  FitsImageViewer: ({
    children,
    imageUrl,
    label,
  }: {
    children?: ReactNode;
    imageUrl: string;
    label: string;
  }) => (
    <div
      data-testid="fits-viewer"
      data-url={imageUrl}
      role="img"
      aria-label={label}
    >
      {children}
    </div>
  ),
}));

vi.mock("@/features/images/components/source-markers", () => ({
  SourceMarkers: ({ sources }: { sources: unknown[] }) => (
    <div data-testid="point-markers" data-count={sources.length} />
  ),
}));

vi.mock("@/features/images/components/extended-source-markers", () => ({
  ExtendedSourceMarkers: ({ sources }: { sources: unknown[] }) => (
    <div data-testid="extended-markers" data-count={sources.length} />
  ),
}));

const SOURCES: SourceOverlays = {
  pointSources: [],
  extendedSources: [],
  gaiaPointIds: new Set(),
  gaiaExtendedIds: new Set(),
};

function renderSection(
  overrides: Partial<Parameters<typeof RenderedFitsSection>[0]> = {},
) {
  return render(
    <RenderedFitsSection
      isPending={false}
      isError={false}
      error={undefined}
      rendered={undefined}
      imageUrl={undefined}
      label="M31"
      sources={SOURCES}
      {...overrides}
    />,
  );
}

describe("RenderedFitsSection", () => {
  it("shows the render skeleton while the render query is pending", () => {
    renderSection({ isPending: true });

    const loading = screen.getByTestId("render-loading");
    expect(loading).toBeInTheDocument();
    expect(loading.querySelectorAll('[data-slot="skeleton"]')).toHaveLength(6);
  });

  it("shows the render error with the query message", () => {
    renderSection({ isError: true, error: new Error("sin datos") });

    expect(screen.getByTestId("render-error")).toHaveTextContent(
      "Error al renderizar: sin datos",
    );
  });

  it("keeps the skeleton until the rendered blob has an object URL", () => {
    renderSection({ rendered: new Blob(["fits"]) });

    expect(screen.getByTestId("render-loading")).toBeInTheDocument();
    expect(
      screen.queryByText("No hay imagen disponible."),
    ).not.toBeInTheDocument();
  });

  it("shows the viewer and both overlay layers when an image URL exists", () => {
    renderSection({
      rendered: new Blob(["fits"]),
      imageUrl: "blob:render",
      sources: {
        ...SOURCES,
        pointSources: [{ id: 1 } as never],
        extendedSources: [{ id: 2 } as never],
      },
    });

    expect(screen.getByTestId("fits-viewer")).toHaveAttribute(
      "data-url",
      "blob:render",
    );
    expect(screen.getByTestId("fits-viewer")).toHaveAttribute(
      "aria-label",
      "M31",
    );
    expect(screen.getByTestId("point-markers")).toHaveAttribute(
      "data-count",
      "1",
    );
    expect(screen.getByTestId("extended-markers")).toHaveAttribute(
      "data-count",
      "1",
    );
  });

  it("explains that there is no image when nothing was rendered", () => {
    renderSection();

    expect(screen.getByText("No hay imagen disponible.")).toBeInTheDocument();
  });
});

describe("useRenderedObjectUrl", () => {
  const createObjectURL = vi.fn(() => "blob:render");
  const revokeObjectURL = vi.fn();

  beforeEach(() => {
    createObjectURL.mockClear();
    revokeObjectURL.mockClear();
    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = revokeObjectURL;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("creates and revokes the URL for a rendered blob", async () => {
    const blob = new Blob(["fits"]);
    const { result, unmount } = renderHook(() => useRenderedObjectUrl(blob));

    await waitFor(() => expect(result.current).toBe("blob:render"));
    expect(createObjectURL).toHaveBeenCalledWith(blob);

    unmount();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:render");
  });

  it("clears the URL when the rendered value stops being a blob", async () => {
    const blob = new Blob(["fits"]);
    const initialProps: { value: unknown } = { value: blob };
    const { result, rerender } = renderHook(
      ({ value }: { value: unknown }) => useRenderedObjectUrl(value),
      { initialProps },
    );

    await waitFor(() => expect(result.current).toBe("blob:render"));
    rerender({ value: undefined });

    await waitFor(() => expect(result.current).toBeUndefined());
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:render");
  });

  it("returns undefined and creates no URL for non-blob data", () => {
    const { result } = renderHook(() => useRenderedObjectUrl({ done: true }));

    expect(result.current).toBeUndefined();
    expect(createObjectURL).not.toHaveBeenCalled();
  });
});
