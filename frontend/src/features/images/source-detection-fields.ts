import type {
  ExtendedDetectionParams,
  PointDetectionParams,
} from "./source-detection";

export type DetectionField<K extends string> = {
  key: K;
  label: string;
  step: string;
  help: string;
  glossaryId: string;
};

export const POINT_FIELDS: DetectionField<keyof PointDetectionParams>[] = [
  {
    key: "fwhm",
    label: "FWHM",
    step: "0.1",
    help: "Ancho a media altura del núcleo estelar, en píxeles. Valores más altos buscan estrellas más extendidas.",
    glossaryId: "fwhm",
  },
  {
    key: "sigma",
    label: "Sigma",
    step: "0.1",
    help: "Umbral de detección en RMS del fondo. Más alto exige picos más contrastados y suele devolver menos fuentes.",
    glossaryId: "sigma",
  },
  {
    key: "min_snr",
    label: "SNR mínimo",
    step: "0.1",
    help: "Relación señal/ruido mínima para conservar un pico. Por debajo de este valor se descarta.",
    glossaryId: "snr",
  },
  {
    key: "min_score",
    label: "Score mínimo",
    step: "0.01",
    help: "Puntuación de relevancia (0 a 1) que mezcla aspecto visual y forma. Filtra candidatos poco convincentes.",
    glossaryId: "score",
  },
  {
    key: "min_distance",
    label: "Distancia mínima",
    step: "0.1",
    help: "Separación mínima entre picos, en píxeles. Evita marcar dos veces la misma estrella.",
    glossaryId: "min-distance",
  },
  {
    key: "visual_weight",
    label: "Peso visual",
    step: "0.05",
    help: "Cuánto pesa el aspecto visual frente a la morfología al calcular el score (0 = solo forma, 1 = solo visual).",
    glossaryId: "visual-weight",
  },
  {
    key: "visual_area_radius",
    label: "Radio visual",
    step: "0.1",
    help: "Radio en píxeles del parche alrededor del pico usado para medir área, flujo y pico aparentes.",
    glossaryId: "visual-area-radius",
  },
  {
    key: "visual_area_sigma",
    label: "Sigma visual",
    step: "0.1",
    help: "Umbral local del parche visual, en RMS del fondo. Define qué píxeles cuentan como parte de la fuente.",
    glossaryId: "visual-area-sigma",
  },
  {
    key: "max_sources",
    label: "Máximo de fuentes",
    step: "1",
    help: "Tope de fuentes a devolver, ordenadas por relevancia. 0 significa sin límite.",
    glossaryId: "max-sources",
  },
];

export const EXTENDED_FIELDS: DetectionField<keyof ExtendedDetectionParams>[] =
  [
    {
      key: "ext_sigma",
      label: "Sigma",
      step: "0.1",
      help: "Umbral en RMS del fondo para abrir regiones. Más alto exige nebulosas más contrastadas.",
      glossaryId: "ext-sigma",
    },
    {
      key: "ext_smooth_sigma",
      label: "Suavizado",
      step: "0.1",
      help: "Suavizado gaussiano previo en píxeles. Muy bajo deja ruido; muy alto funde estructuras finas.",
      glossaryId: "ext-smooth-sigma",
    },
    {
      key: "ext_min_area",
      label: "Área mínima",
      step: "10",
      help: "Área mínima de la región en píxeles. Estructuras más chicas se descartan.",
      glossaryId: "ext-min-area",
    },
    {
      key: "ext_max_area",
      label: "Área máxima",
      step: "10",
      help: "Área máxima de la región en píxeles. 0 significa sin límite.",
      glossaryId: "ext-max-area",
    },
    {
      key: "ext_bin_factor",
      label: "Factor de bin",
      step: "1",
      help: "Agrupado de píxeles que hace el detector. No cambia el resultado, solo el costo.",
      glossaryId: "ext-binning",
    },
    {
      key: "ext_closing_iterations",
      label: "Cierre",
      step: "1",
      help: "Pasadas de cierre morfológico que rellenan huecos y unen bordes. 0 desactiva.",
      glossaryId: "ext-closing",
    },
    {
      key: "ext_opening_iterations",
      label: "Apertura",
      step: "1",
      help: "Pasadas de apertura que cortan protuberancias finas y ruido. 0 desactiva.",
      glossaryId: "ext-opening",
    },
    {
      key: "ext_min_score",
      label: "Score mínimo",
      step: "0.01",
      help: "Puntuación de relevancia (0 a 1) mínima para conservar una estructura.",
      glossaryId: "score",
    },
    {
      key: "ext_max_sources",
      label: "Máximo de estructuras",
      step: "1",
      help: "Tope de estructuras a devolver, ordenadas por relevancia. 0 significa sin límite.",
      glossaryId: "max-sources",
    },
  ];

export function pointToDraft(
  params: PointDetectionParams,
): Record<keyof PointDetectionParams, string> {
  return {
    fwhm: String(params.fwhm),
    sigma: String(params.sigma),
    min_snr: String(params.min_snr),
    min_score: String(params.min_score),
    min_distance: String(params.min_distance),
    visual_weight: String(params.visual_weight),
    visual_area_radius: String(params.visual_area_radius),
    visual_area_sigma: String(params.visual_area_sigma),
    max_sources: String(params.max_sources),
  };
}

export function extendedToDraft(
  params: ExtendedDetectionParams,
): Record<keyof ExtendedDetectionParams, string> {
  return {
    ext_sigma: String(params.ext_sigma),
    ext_smooth_sigma: String(params.ext_smooth_sigma),
    ext_min_area: String(params.ext_min_area),
    ext_max_area: String(params.ext_max_area),
    ext_bin_factor: String(params.ext_bin_factor),
    ext_closing_iterations: String(params.ext_closing_iterations),
    ext_opening_iterations: String(params.ext_opening_iterations),
    ext_min_score: String(params.ext_min_score),
    ext_max_sources: String(params.ext_max_sources),
  };
}

export function parsePointDraft(
  draft: Record<keyof PointDetectionParams, string>,
): PointDetectionParams | null {
  const fwhm = readNumber(draft.fwhm);
  const sigma = readNumber(draft.sigma);
  const minSnr = readNumber(draft.min_snr);
  const minScore = readNumber(draft.min_score);
  const minDistance = readNumber(draft.min_distance);
  const visualWeight = readNumber(draft.visual_weight);
  const visualAreaRadius = readNumber(draft.visual_area_radius);
  const visualAreaSigma = readNumber(draft.visual_area_sigma);
  const maxSources = readNumber(draft.max_sources);
  if (
    fwhm === null ||
    sigma === null ||
    minSnr === null ||
    minScore === null ||
    minDistance === null ||
    visualWeight === null ||
    visualAreaRadius === null ||
    visualAreaSigma === null ||
    maxSources === null
  ) {
    return null;
  }
  return {
    fwhm,
    sigma,
    min_snr: minSnr,
    min_score: minScore,
    min_distance: minDistance,
    visual_weight: visualWeight,
    visual_area_radius: visualAreaRadius,
    visual_area_sigma: visualAreaSigma,
    max_sources: Math.round(maxSources),
  };
}

export function parseExtendedDraft(
  draft: Record<keyof ExtendedDetectionParams, string>,
): ExtendedDetectionParams | null {
  const extSigma = readNumber(draft.ext_sigma);
  const extSmoothSigma = readNumber(draft.ext_smooth_sigma);
  const extMinArea = readNumber(draft.ext_min_area);
  const extMaxArea = readNumber(draft.ext_max_area);
  const extBinFactor = readNumber(draft.ext_bin_factor);
  const extClosing = readNumber(draft.ext_closing_iterations);
  const extOpening = readNumber(draft.ext_opening_iterations);
  const extMinScore = readNumber(draft.ext_min_score);
  const extMaxSources = readNumber(draft.ext_max_sources);
  if (
    extSigma === null ||
    extSmoothSigma === null ||
    extMinArea === null ||
    extMaxArea === null ||
    extBinFactor === null ||
    extClosing === null ||
    extOpening === null ||
    extMinScore === null ||
    extMaxSources === null
  ) {
    return null;
  }
  return {
    ext_sigma: extSigma,
    ext_smooth_sigma: extSmoothSigma,
    ext_min_area: Math.round(extMinArea),
    ext_max_area: Math.round(extMaxArea),
    ext_bin_factor: Math.round(extBinFactor),
    ext_closing_iterations: Math.round(extClosing),
    ext_opening_iterations: Math.round(extOpening),
    ext_min_score: extMinScore,
    ext_max_sources: Math.round(extMaxSources),
  };
}

export function readNumber(raw: string): number | null {
  const trimmed = raw.trim();
  if (trimmed === "") {
    return null;
  }
  const numeric = Number(trimmed);
  return Number.isFinite(numeric) ? numeric : null;
}
