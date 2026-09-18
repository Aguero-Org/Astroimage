import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { HelpHint } from "./help-hint";

vi.mock("@tanstack/react-router", () => ({
  Link: ({
    to,
    hash,
    children,
    ...props
  }: {
    to: string;
    hash?: string;
    children: ReactNode;
  }) => (
    <a href={hash ? `${to}#${hash}` : to} {...props}>
      {children}
    </a>
  ),
}));

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

  it("links the tooltip to the matching glossary anchor", async () => {
    const user = userEvent.setup();
    render(
      <TooltipProvider delayDuration={0}>
        <HelpHint label="FWHM" testId="help-fwhm" glossaryId="fwhm">
          Ancho a media altura del núcleo estelar.
        </HelpHint>
      </TooltipProvider>,
    );

    await user.hover(screen.getByTestId("help-fwhm"));
    const link = await screen.findByTestId("help-fwhm-glossary");
    expect(link).toHaveAttribute("href", "/glossary#fwhm");
  });
});
