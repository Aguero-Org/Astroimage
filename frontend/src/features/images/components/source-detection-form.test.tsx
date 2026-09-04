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

  it("allows clearing a numeric field without restoring zero", async () => {
    const user = userEvent.setup();
    render(<SourceDetectionForm isPending={false} onSubmit={vi.fn()} />);

    const fwhm = screen.getByLabelText("FWHM");
    await user.clear(fwhm);

    expect(fwhm).toHaveValue(null);
  });

  it("does not submit while a field is empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<SourceDetectionForm isPending={false} onSubmit={onSubmit} />);

    await user.clear(screen.getByLabelText("FWHM"));
    await user.click(screen.getByRole("button", { name: "Detectar fuentes" }));

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the typed value after clearing a field", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<SourceDetectionForm isPending={false} onSubmit={onSubmit} />);

    const fwhm = screen.getByLabelText("FWHM");
    await user.clear(fwhm);
    await user.type(fwhm, "3.2");
    await user.click(screen.getByRole("button", { name: "Detectar fuentes" }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ fwhm: 3.2 }),
    );
  });
});
