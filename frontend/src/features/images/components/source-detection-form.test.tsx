import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { SourcePresetResponse } from "@/api/generated/model";
import { TooltipProvider } from "@/components/ui/tooltip";
import { type BestPreset, NO_MEASUREMENT_SUMMARY } from "../best-preset";
import {
  DEFAULT_SOURCE_DETECTION_PARAMS,
  type SourceDetectionParams,
} from "../source-detection";
import { SourceDetectionForm } from "./source-detection-form";

function renderForm(props: {
  isPending: boolean;
  bestPreset?: BestPreset;
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

describe("SourceDetectionForm con preset recomendado", () => {
  const measured: SourcePresetResponse = {
    point_config: { fwhm: 9.5, min_distance: 8 },
    extended_config: { smooth_sigma: 16, min_area: 900 },
    baseline_point_config: {},
    baseline_extended_config: {},
    evidence: { measured_fwhm: 9.5, fwhm_samples: 12, fwhm_spread: 1.2 },
  };

  function renderWithBestPreset(
    overrides: Partial<BestPreset> = {},
    onSubmit: (params: SourceDetectionParams) => void = vi.fn(),
  ) {
    return renderForm({
      isPending: false,
      bestPreset: {
        isPending: false,
        isError: false,
        data: undefined,
        request: vi.fn(),
        ...overrides,
      },
      onSubmit,
    });
  }

  it("no muestra el control si la imagen no puede pedirlo", () => {
    renderForm({ isPending: false, onSubmit: vi.fn() });

    expect(screen.queryByTestId("source-best-preset")).not.toBeInTheDocument();
  });

  it("pide el preset recomendado al pulsar el botón", async () => {
    const request = vi.fn();
    const user = userEvent.setup();
    renderWithBestPreset({ request });

    await user.click(screen.getByTestId("source-best-preset"));

    expect(request).toHaveBeenCalledTimes(1);
  });

  it("rellena los campos cuando llega la medición", () => {
    renderWithBestPreset({ data: measured });

    expect(screen.getByTestId("source-field-fwhm")).toHaveValue("9.5");
    expect(screen.getByTestId("source-field-min_distance")).toHaveValue("8");
    expect(screen.getByTestId("source-field-ext_smooth_sigma")).toHaveValue(
      "16",
    );
    expect(screen.getByTestId("source-field-ext_min_area")).toHaveValue("900");
  });

  it("deja intactos los parámetros que la medición no toca", () => {
    renderWithBestPreset({ data: measured });

    expect(screen.getByTestId("source-field-min_snr")).toHaveValue(
      String(DEFAULT_SOURCE_DETECTION_PARAMS.min_snr),
    );
    expect(screen.getByTestId("source-field-sigma")).toHaveValue(
      String(DEFAULT_SOURCE_DETECTION_PARAMS.sigma),
    );
  });

  it("conserva lo que el usuario había escrito antes de pedirlo", async () => {
    const user = userEvent.setup();
    const withPreset = (data: SourcePresetResponse | undefined) => (
      <TooltipProvider delayDuration={0}>
        <SourceDetectionForm
          isPending={false}
          bestPreset={{
            isPending: false,
            isError: false,
            data,
            request: vi.fn(),
          }}
          onSubmit={vi.fn()}
        />
      </TooltipProvider>
    );
    const { rerender } = render(withPreset(undefined));

    await user.clear(screen.getByTestId("source-field-min_snr"));
    await user.type(screen.getByTestId("source-field-min_snr"), "42");
    rerender(withPreset(measured));

    expect(screen.getByTestId("source-field-min_snr")).toHaveValue("42");
    expect(screen.getByTestId("source-field-fwhm")).toHaveValue("9.5");
  });

  it("muestra el FWHM medido y cuántas fuentes se usaron", () => {
    renderWithBestPreset({ data: measured });

    expect(screen.getByTestId("source-best-preset-summary")).toHaveTextContent(
      "FWHM 9.5 px sobre 12 fuentes",
    );
  });

  it("explica que no se pudo medir cuando la imagen no tiene fuentes", () => {
    renderWithBestPreset({
      data: { ...measured, evidence: { fwhm_samples: 0 } },
    });

    expect(screen.getByTestId("source-best-preset-summary")).toHaveTextContent(
      NO_MEASUREMENT_SUMMARY,
    );
  });

  it("avisa cuando la API falla", () => {
    renderWithBestPreset({ isError: true });

    expect(screen.getByTestId("source-best-preset-summary")).toHaveTextContent(
      "No se pudo pedir el recomendado",
    );
  });

  it("deshabilita el botón mientras se está midiendo", () => {
    renderWithBestPreset({ isPending: true });

    expect(screen.getByTestId("source-best-preset")).toBeDisabled();
    expect(screen.getByTestId("source-best-preset")).toHaveTextContent(
      "Midiendo…",
    );
  });

  it("expone un control de ayuda para el preset recomendado", () => {
    renderWithBestPreset();

    expect(screen.getByTestId("source-help-best-preset")).toBeInTheDocument();
  });
});
