import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MastSourceLink, mastFileUrl } from "../mast-source-link";

describe("MastSourceLink", () => {
  it("links the MAST data URI to the original file", () => {
    const dataUri = "mast:HST/product/u2kj0102t_drw.fits";
    render(<MastSourceLink dataUri={dataUri} />);

    const link = screen.getByRole("link", { name: dataUri });
    expect(link).toHaveAttribute("href", mastFileUrl(dataUri));
    expect(link).toHaveAttribute("target", "_blank");
  });
});
