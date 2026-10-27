import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MastSourceLink, mastFileUrl } from "../mast-source-link";
import { StoredFitsLink, storedFitsUrl } from "../stored-fits-link";

describe("MastSourceLink", () => {
  it("links the MAST data URI to the original file", () => {
    const dataUri = "mast:HST/product/u2kj0102t_drw.fits";
    render(
      <TooltipProvider>
        <MastSourceLink dataUri={dataUri} />
      </TooltipProvider>,
    );

    const link = screen.getByRole("link", {
      name: `Archivo original en MAST: ${dataUri}`,
    });
    expect(link).toHaveAttribute("href", mastFileUrl(dataUri));
    expect(link).toHaveAttribute("target", "_blank");
  });
});

describe("StoredFitsLink", () => {
  it("links a local import to the file served by the API", () => {
    render(
      <TooltipProvider>
        <StoredFitsLink recordId="record-1" filename="local.fits" />
      </TooltipProvider>,
    );

    const link = screen.getByRole("link", { name: "Descargar local.fits" });
    expect(link).toHaveAttribute("href", storedFitsUrl("record-1"));
  });
});
