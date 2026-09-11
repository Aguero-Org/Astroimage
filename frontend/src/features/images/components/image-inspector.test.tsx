import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ImageInspector } from "./image-inspector";

describe("ImageInspector", () => {
  it("keeps the drawer closed until the hamburger is clicked", async () => {
    const user = userEvent.setup();
    render(
      <TooltipProvider delayDuration={0}>
        <div className="relative h-96">
          <ImageInspector
            title={<h1 data-testid="image-detail-title">M31</h1>}
            view={<p>Formulario de vista</p>}
            sources={<p>Formulario de fuentes</p>}
            archive={<p>Metadatos de archivo</p>}
            selection={<p>Sin selección</p>}
          />
        </div>
      </TooltipProvider>,
    );

    expect(screen.getByTestId("inspector-toggle")).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    expect(screen.getByTestId("inspector-drawer")).toHaveAttribute(
      "data-state",
      "collapsed",
    );
    await user.click(screen.getByTestId("inspector-toggle"));
    expect(screen.getByTestId("inspector-toggle")).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(screen.getByTestId("inspector-drawer")).toHaveAttribute(
      "data-state",
      "expanded",
    );
    expect(screen.getByText("Formulario de fuentes")).toBeVisible();
    expect(screen.queryByText("Formulario de vista")).not.toBeInTheDocument();
    expect(screen.getByTestId("inspector-section-view")).toBeInTheDocument();
    expect(
      screen.getByTestId("inspector-section-selection"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("inspector-section-archive")).toBeInTheDocument();
    expect(screen.getByTestId("image-detail-title")).toBeInTheDocument();
    expect(
      screen.getByTestId("inspector-toggle").parentElement,
    ).toContainElement(screen.getByTestId("image-detail-title"));
  });
});
