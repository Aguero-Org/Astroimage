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
          <ImageInspector sources={<p>Formulario de fuentes</p>} />
        </div>
      </TooltipProvider>,
    );

    expect(screen.getByTestId("inspector-drawer")).not.toBeVisible();
    await user.click(screen.getByTestId("inspector-toggle"));
    expect(screen.getByTestId("inspector-drawer")).toBeVisible();
    expect(screen.getByText("Formulario de fuentes")).toBeVisible();
    expect(screen.getByTestId("inspector-section-view")).toBeInTheDocument();
    expect(
      screen.getByTestId("inspector-section-selection"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("inspector-section-archive")).toBeInTheDocument();
  });
});
