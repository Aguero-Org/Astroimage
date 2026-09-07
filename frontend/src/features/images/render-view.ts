import type { RenderFitsImageParams } from "@/api/generated/model";
import type { NamedPreset } from "./named-preset";

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

export const RENDER_PRESETS: NamedPreset<RenderViewParams>[] = [
  {
    id: "estandar",
    label: "Estándar",
    outcome:
      "Estrellas y cielo se ven a la vez, sin quemar lo más brillante ni pintar el ruido.",
    hint: "Usala la primera vez que abrís el recorte.",
    values: DEFAULT_RENDER_PARAMS,
  },
  {
    id: "cielo-profundo",
    label: "Cielo profundo",
    outcome:
      "El fondo y las nubes débiles se ven más; los núcleos muy brillantes se aplastan un poco.",
    hint: "Usala si hay nebulosa, polvo o un objeto brillante con halo. No si solo te importan las estrellas puntuales: el cielo se llena de grano.",
    values: {
      stretch: "asinh",
      limits: "percentiles",
      colormap: "grey",
      pmin: 0.5,
      pmax: 99.5,
      gamma: 1.2,
    },
  },
  {
    id: "zscale",
    label: "Zscale",
    outcome:
      "Recupera detalle cuando la imagen se ve casi negra o casi blanca por un destello o un pixel disparado.",
    hint: "Usala si el estándar deja el campo vacío o saturado. Si ya se ve bien, el recorte puede cambiar un poco de una vez a otra.",
    values: {
      stretch: "sqrt",
      limits: "zscale",
      colormap: "grey",
      pmin: 1,
      pmax: 99,
      gamma: 1,
    },
  },
  {
    id: "nucleos",
    label: "Núcleos",
    outcome:
      "Se nota quién es realmente más brillante; el cielo queda más oscuro.",
    hint: "Usala para mirar centros, picos y saturación. No para cazar estructura débil.",
    values: {
      stretch: "linear",
      limits: "percentiles",
      colormap: "grey",
      pmin: 5,
      pmax: 99,
      gamma: 1,
    },
  },
  {
    id: "color",
    label: "Color",
    outcome:
      "La misma imagen, en una escala de color que sigue yendo de oscuro a claro.",
    hint: "Usala si en gris no distinguís niveles. No cambia las fuentes ni inventa nebulosa.",
    values: {
      ...DEFAULT_RENDER_PARAMS,
      colormap: "cube_helix",
    },
  },
];
