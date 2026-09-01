import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SourceDetectionForm } from "./source-detection-form";

describe("SourceDetectionForm", () => {
  it("submits default detection parameters", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<SourceDetectionForm isPending={false} onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: "Detectar fuentes" }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        fwhm: 5.5,
        sigma: 9,
        min_snr: 6,
        max_sources: 50,
      }),
    );
  });

  it("exposes a help control for each detection parameter", () => {
    render(<SourceDetectionForm isPending={false} onSubmit={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: "Ayuda: FWHM" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Ayuda: Máximo de fuentes" }),
    ).toBeInTheDocument();
  });
});
