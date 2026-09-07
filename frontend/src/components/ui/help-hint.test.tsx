import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { HelpHint } from "./help-hint";

describe("HelpHint", () => {
  it("exposes a labeled help control", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <HelpHint label="FWHM" testId="help-fwhm">
          Ancho a media altura del núcleo estelar.
        </HelpHint>
      </TooltipProvider>,
    );

    expect(screen.getByTestId("help-fwhm")).toHaveAttribute(
      "aria-label",
      "Ayuda: FWHM",
    );
  });
});
