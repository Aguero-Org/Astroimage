import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

  it("places a glossary book link next to the help control", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <HelpHint label="FWHM" testId="help-fwhm" glossaryId="fwhm">
          Ancho a media altura del núcleo estelar.
        </HelpHint>
      </TooltipProvider>,
    );

    expect(screen.getByTestId("help-fwhm-glossary")).toHaveAttribute(
      "href",
      "/glossary#fwhm",
    );
  });

  it("explains the glossary book link on hover", async () => {
    const user = userEvent.setup();
    render(
      <TooltipProvider delayDuration={0}>
        <HelpHint label="FWHM" testId="help-fwhm" glossaryId="fwhm">
          Ancho a media altura del núcleo estelar.
        </HelpHint>
      </TooltipProvider>,
    );

    await user.hover(screen.getByTestId("help-fwhm-glossary"));
    expect(await screen.findByText("Ver en el glosario")).toBeInTheDocument();
  });
});
