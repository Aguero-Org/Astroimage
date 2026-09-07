import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SourceDetectionForm } from "./source-detection-form";

function renderForm(props: {
  isPending: boolean;
  onSubmit: ReturnType<typeof vi.fn>;
}) {
  return render(
    <TooltipProvider delayDuration={0}>
      <SourceDetectionForm {...props} />
    </TooltipProvider>,
  );
}

describe("SourceDetectionForm", () => {
  it("submits default detection parameters", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ isPending: false, onSubmit });

    expect(screen.getByTestId("source-detection-form")).toBeInTheDocument();
    await user.click(screen.getByTestId("source-detect-submit"));

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
    renderForm({ isPending: false, onSubmit: vi.fn() });

    expect(screen.getByTestId("source-help-fwhm")).toBeInTheDocument();
    expect(screen.getByTestId("source-help-max_sources")).toBeInTheDocument();
  });

  it("allows clearing a numeric field without restoring zero", async () => {
    const user = userEvent.setup();
    renderForm({ isPending: false, onSubmit: vi.fn() });

    const fwhm = screen.getByTestId("source-field-fwhm");
    await user.clear(fwhm);

    expect(fwhm).toHaveValue(null);
  });

  it("does not submit while a field is empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ isPending: false, onSubmit });

    await user.clear(screen.getByTestId("source-field-fwhm"));
    await user.click(screen.getByTestId("source-detect-submit"));

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the typed value after clearing a field", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ isPending: false, onSubmit });

    const fwhm = screen.getByTestId("source-field-fwhm");
    await user.clear(fwhm);
    await user.type(fwhm, "3.2");
    await user.click(screen.getByTestId("source-detect-submit"));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ fwhm: 3.2 }),
    );
  });
});
