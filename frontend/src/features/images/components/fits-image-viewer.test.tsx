import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FitsImageViewer } from "./fits-image-viewer";

vi.mock("@cellbytes/react-openseadragon", () => ({
  useOpenseadragon: () => ({
    setContainerElement: vi.fn(),
  }),
  ViewerStateProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="osd-provider">{children}</div>
  ),
  TiledImage: ({ tileSource }: { tileSource: { url?: string } | string }) => (
    <div data-testid="tiled-image">
      {typeof tileSource === "string" ? tileSource : (tileSource.url ?? "")}
    </div>
  ),
  useViewer: () => ({ viewer: null }),
  useViewerEvent: vi.fn(),
}));

describe("FitsImageViewer", () => {
  it("mounts the OpenSeadragon container, toolbar, and tiled image", () => {
    render(
      <FitsImageViewer
        imageUrl="blob:http://localhost/fits-preview"
        label="m31 render"
      />,
    );

    expect(screen.getByRole("img", { name: "m31 render" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Acercar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Alejar" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Ajustar a la vista" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Pantalla completa" }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("tiled-image")).toHaveTextContent(
      "blob:http://localhost/fits-preview",
    );
  });
});
