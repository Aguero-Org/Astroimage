import { z } from "zod";
import type { RenderFitsImageParams } from "@/api/generated/model";
import type { NamedPreset } from "./named-preset";

export type RenderViewParams = Required<
  Pick<
    RenderFitsImageParams,
    "stretch" | "limits" | "colormap" | "pmin" | "pmax" | "gamma"
  >
>;

type RenderNumericKey = "pmin" | "pmax" | "gamma";

export type RenderDraft = Omit<RenderViewParams, RenderNumericKey> &
  Record<RenderNumericKey, string>;

export function paramsToDraft(params: RenderViewParams): RenderDraft {
  return {
    ...params,
    pmin: String(params.pmin),
    pmax: String(params.pmax),
    gamma: String(params.gamma),
  };
}

const numericDraftField = z
  .string()
  .refine((value) => Number.isFinite(Number(value)));

export const renderDraftSchema: z.ZodType<RenderDraft, RenderDraft> = z
  .object({
    stretch: z.enum(["linear", "sqrt", "log", "asinh"]),
    limits: z.enum(["percentiles", "zscale"]),
    colormap: z.enum(["grey", "inverse", "heat", "rainbow", "cube_helix"]),
    pmin: numericDraftField,
    pmax: numericDraftField,
    gamma: numericDraftField,
  })
  .refine((draft) => Number(draft.pmin) < Number(draft.pmax));

export function parseRenderDraft(draft: RenderDraft): RenderViewParams | null {
  const parsed = renderDraftSchema.safeParse(draft);
  if (!parsed.success) {
    return null;
  }
  return {
    stretch: parsed.data.stretch,
    limits: parsed.data.limits,
    colormap: parsed.data.colormap,
    pmin: Number(parsed.data.pmin),
    pmax: Number(parsed.data.pmax),
    gamma: Number(parsed.data.gamma),
  };
}

export const DEFAULT_RENDER_PARAMS: RenderViewParams = {
  stretch: "linear",
  limits: "percentiles",
  colormap: "grey",
  pmin: 1,
  pmax: 99,
  gamma: 0.5,
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
    id: "equilibrio",
    label: "Equilibrio",
    outcome:
      "Estrellas y cielo se ven a la vez, sin quemar lo más brillante ni pintar el ruido.",
    hint: "Primera vez que abrís el recorte.",
    values: DEFAULT_RENDER_PARAMS,
  },
  {
    id: "mucho-ruido",
    label: "Mucho ruido",
    outcome:
      "El grano del fondo se recorta; se pierde un poco de brillo débil.",
    hint: "El cielo se ve salpicado o sucio. No si lo que buscás es precisamente ese fondo.",
    values: {
      stretch: "sqrt",
      limits: "percentiles",
      colormap: "grey",
      pmin: 3,
      pmax: 99,
      gamma: 0.6,
    },
  },
  {
    id: "mucho-brillo",
    label: "Mucho brillo",
    outcome: "Los núcleos dejan de estar quemados; el cielo queda más oscuro.",
    hint: "Hay centros saturados o un destello que se come el recorte.",
    values: {
      stretch: "asinh",
      limits: "percentiles",
      colormap: "grey",
      pmin: 0.5,
      pmax: 98,
      gamma: 0.5,
    },
  },
  {
    id: "poco-contraste",
    label: "Poco contraste",
    outcome:
      "El recorte se adapta al ruido local cuando casi todo se ve negro o blanco.",
    hint: "Equilibrio deja el campo vacío o una mancha única.",
    values: {
      stretch: "sqrt",
      limits: "zscale",
      colormap: "grey",
      pmin: 1,
      pmax: 99,
      gamma: 0.8,
    },
  },
  {
    id: "estructura-debil",
    label: "Estructura débil",
    outcome: "Halos, polvo y nubes se ven más; los picos se aplastan un poco.",
    hint: "Nebulosa o un objeto brillante con envoltura. No para un campo solo de estrellas nítidas.",
    values: {
      stretch: "asinh",
      limits: "percentiles",
      colormap: "grey",
      pmin: 0.25,
      pmax: 99.5,
      gamma: 1.3,
    },
  },
];
