import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ImageSearch } from "./image-search";

describe("ImageSearch", () => {
  it("submits the typed query from the hero layout", async () => {
    const onSearch = vi.fn();
    const user = userEvent.setup();
    render(
      <TooltipProvider delayDuration={0}>
        <ImageSearch variant="hero" value="" onSearch={onSearch} />
      </TooltipProvider>,
    );

    await user.type(screen.getByTestId("search-input"), "orion");
    await user.click(screen.getByTestId("search-submit"));

    expect(onSearch).toHaveBeenCalledWith("orion");
    expect(screen.getByTestId("help-objeto-glossary")).toHaveAttribute(
      "href",
      "/glossary#objeto",
    );
  });

  it("uses a compact control in the navbar layout", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <ImageSearch variant="navbar" value="" onSearch={vi.fn()} />
      </TooltipProvider>,
    );

    const field = screen.getByTestId("search-input");
    expect(field.className).toContain("w-36");
    expect(screen.getByTestId("search-submit").className).toContain("h-8");
  });
});
