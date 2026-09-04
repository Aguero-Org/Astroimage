import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { FitsImageViewerToolbar } from "./fits-image-viewer-toolbar";

const viewport = {
  zoomBy: vi.fn(),
  applyConstraints: vi.fn(),
  goHome: vi.fn(),
};
const viewer = {
  viewport,
  setFullScreen: vi.fn(),
};

vi.mock("@cellbytes/react-openseadragon", () => ({
  useViewer: () => ({ viewer }),
  useViewerEvent: vi.fn(),
}));

describe("FitsImageViewerToolbar", () => {
  it("zooms, fits, and toggles full screen through the viewer API", async () => {
    const user = userEvent.setup();
    render(<FitsImageViewerToolbar />);

    await user.click(screen.getByRole("button", { name: "Acercar" }));
    expect(viewport.zoomBy).toHaveBeenCalledWith(1.2);
    expect(viewport.applyConstraints).toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Alejar" }));
    expect(viewport.zoomBy).toHaveBeenCalledWith(1 / 1.2);

    await user.click(
      screen.getByRole("button", { name: "Ajustar a la vista" }),
    );
    expect(viewport.goHome).toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Pantalla completa" }));
    expect(viewer.setFullScreen).toHaveBeenCalledWith(true);
  });
});
