import type { RenderFitsImageParams } from "@/api/generated/model";

export type RenderViewParams = Required<
  Pick<
    RenderFitsImageParams,
    "stretch" | "limits" | "colormap" | "pmin" | "pmax" | "gamma"
  >
>;

export const DEFAULT_RENDER_PARAMS: RenderViewParams = {
  stretch: "sqrt",
  limits: "percentiles",
  colormap: "grey",
  pmin: 1,
  pmax: 99,
  gamma: 1,
};

export const STRETCH_OPTIONS = [
  { value: "linear", label: "Lineal" },
  { value: "sqrt", label: "Raíz cuadrada" },
  { value: "log", label: "Logarítmico" },
  { value: "asinh", label: "Asinh" },
] as const;

export const LIMITS_OPTIONS = [
  { value: "percentiles", label: "Percentiles" },
  { value: "zscale", label: "ZScale" },
] as const;

export const COLORMAP_OPTIONS = [
  { value: "grey", label: "Gris" },
  { value: "inverse", label: "Inverso" },
  { value: "heat", label: "Calor" },
  { value: "rainbow", label: "Arcoíris" },
  { value: "cube_helix", label: "Cube helix" },
] as const;
