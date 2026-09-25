import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import {
  DEFAULT_SOURCE_DETECTION_PARAMS,
  type SourceDetectionParams,
} from "../source-detection";
import { SourceDetectionForm } from "./source-detection-form";

function renderForm(props: {
  isPending: boolean;
  onSubmit: (params: SourceDetectionParams) => void;
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
        fwhm: 3,
        sigma: 5,
        min_snr: 5,
        max_sources: 50,
      }),
    );
  });

  it("fills detection fields from a named preset", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ isPending: false, onSubmit });

    await user.click(screen.getByTestId("source-preset"));
    await user.click(screen.getByTestId("source-preset-mucho-ruido"));
    await user.click(screen.getByTestId("source-detect-submit"));

    expect(onSubmit).toHaveBeenCalledWith({
      ...DEFAULT_SOURCE_DETECTION_PARAMS,
      fwhm: 3,
      sigma: 10,
      min_snr: 9,
      min_score: 0.35,
      min_distance: 5,
      visual_weight: 0.75,
      visual_area_radius: 7,
      visual_area_sigma: 2.5,
      max_sources: 20,
    });
  });

  it("marks the detection preset as custom after editing a field", async () => {
    const user = userEvent.setup();
    renderForm({ isPending: false, onSubmit: vi.fn() });

    await user.clear(screen.getByTestId("source-field-fwhm"));
    await user.type(screen.getByTestId("source-field-fwhm"), "3.2");
    expect(screen.getByTestId("source-preset")).toHaveTextContent(
      "Personalizado",
    );
  });

  it("restores default detection parameters", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ isPending: false, onSubmit });

    await user.click(screen.getByTestId("source-preset"));
    await user.click(screen.getByTestId("source-preset-muchas-estrellas"));
    await user.click(screen.getByTestId("source-detect-reset"));
    await user.click(screen.getByTestId("source-detect-submit"));

    expect(onSubmit).toHaveBeenCalledWith(DEFAULT_SOURCE_DETECTION_PARAMS);
  });

  it("exposes a help control for each detection parameter", () => {
    renderForm({ isPending: false, onSubmit: vi.fn() });

    expect(screen.getByTestId("source-help-fwhm")).toBeInTheDocument();
    expect(screen.getByTestId("source-help-max_sources")).toBeInTheDocument();
    expect(screen.getByTestId("source-help-ext_sigma")).toBeInTheDocument();
  });

  it("renders point and extended parameter groups", () => {
    renderForm({ isPending: false, onSubmit: vi.fn() });

    expect(screen.getByTestId("source-group-point")).toBeInTheDocument();
    expect(screen.getByTestId("source-group-extended")).toBeInTheDocument();
    expect(screen.getByTestId("source-field-fwhm")).toBeInTheDocument();
    expect(screen.getByTestId("source-field-ext_min_area")).toBeInTheDocument();
  });

  it("keeps the point preset when only an extended field changes", async () => {
    const user = userEvent.setup();
    renderForm({ isPending: false, onSubmit: vi.fn() });

    await user.type(screen.getByTestId("source-field-ext_min_area"), "0");

    expect(screen.getByTestId("source-preset")).toHaveTextContent("Equilibrio");
  });

  it("allows clearing a numeric field without restoring zero", async () => {
    const user = userEvent.setup();
    renderForm({ isPending: false, onSubmit: vi.fn() });

    const fwhm = screen.getByTestId("source-field-fwhm");
    await user.clear(fwhm);

    expect(fwhm).toHaveValue("");
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
