import { CircleHelp } from "lucide-react";
import { type SyntheticEvent, useState } from "react";
import type { DetectSourcesParams } from "@/api/generated/model";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { DEFAULT_SOURCE_DETECTION_PARAMS } from "../source-detection";

type SourceDetectionFormProps = {
  isPending: boolean;
  onSubmit: (params: Omit<DetectSourcesParams, "hdu">) => void;
};

type FieldKey = keyof typeof DEFAULT_SOURCE_DETECTION_PARAMS;

const FIELDS: { key: FieldKey; label: string; step: string; help: string }[] = [
  {
    key: "fwhm",
    label: "FWHM",
    step: "0.1",
    help: "Ancho a media altura del núcleo estelar, en píxeles. Valores más altos buscan estrellas más extendidas.",
  },
  {
    key: "sigma",
    label: "Sigma",
    step: "0.1",
    help: "Umbral de detección en RMS del fondo. Más alto exige picos más contrastados y suele devolver menos fuentes.",
  },
  {
    key: "min_snr",
    label: "SNR mínimo",
    step: "0.1",
    help: "Relación señal/ruido mínima para conservar un pico. Por debajo de este valor se descarta.",
  },
  {
    key: "min_score",
    label: "Score mínimo",
    step: "0.01",
    help: "Puntuación de relevancia (0 a 1) que mezcla aspecto visual y forma. Filtra candidatos poco convincentes.",
  },
  {
    key: "min_distance",
    label: "Distancia mínima",
    step: "0.1",
    help: "Separación mínima entre picos, en píxeles. Evita marcar dos veces la misma estrella.",
  },
  {
    key: "visual_weight",
    label: "Peso visual",
    step: "0.05",
    help: "Cuánto pesa el aspecto visual frente a la morfología al calcular el score (0 = solo forma, 1 = solo visual).",
  },
  {
    key: "visual_area_radius",
    label: "Radio visual",
    step: "0.1",
    help: "Radio en píxeles del parche alrededor del pico usado para medir área, flujo y pico aparentes.",
  },
  {
    key: "visual_area_sigma",
    label: "Sigma visual",
    step: "0.1",
    help: "Umbral local del parche visual, en RMS del fondo. Define qué píxeles cuentan como parte de la fuente.",
  },
  {
    key: "max_sources",
    label: "Máximo de fuentes",
    step: "1",
    help: "Tope de fuentes a devolver, ordenadas por relevancia. 0 significa sin límite.",
  },
];

function paramsToDraft(
  params: typeof DEFAULT_SOURCE_DETECTION_PARAMS,
): Record<FieldKey, string> {
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

function parseDraft(
  draft: Record<FieldKey, string>,
): typeof DEFAULT_SOURCE_DETECTION_PARAMS | null {
  const parsed: Partial<typeof DEFAULT_SOURCE_DETECTION_PARAMS> = {};
  for (const field of FIELDS) {
    const raw = draft[field.key].trim();
    if (raw === "") {
      return null;
    }
    const numeric = Number(raw);
    if (!Number.isFinite(numeric)) {
      return null;
    }
    parsed[field.key] = numeric;
  }
  return {
    ...(parsed as typeof DEFAULT_SOURCE_DETECTION_PARAMS),
    max_sources: Math.round(parsed.max_sources ?? 0),
  };
}

export function SourceDetectionForm({
  isPending,
  onSubmit,
}: Readonly<SourceDetectionFormProps>) {
  const [draft, setDraft] = useState(() =>
    paramsToDraft(DEFAULT_SOURCE_DETECTION_PARAMS),
  );

  function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = parseDraft(draft);
    if (values === null) {
      return;
    }
    onSubmit(values);
  }

  return (
    <TooltipProvider delayDuration={200}>
      <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {FIELDS.map((field) => (
            <div key={field.key} className="flex flex-col gap-1 text-sm">
              <div className="flex items-center gap-1">
                <label htmlFor={field.key} className="text-muted-foreground">
                  {field.label}
                </label>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      className="inline-flex size-4 cursor-help items-center justify-center rounded-full text-muted-foreground hover:text-foreground"
                      aria-label={`Ayuda: ${field.label}`}
                    >
                      <CircleHelp className="size-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs" side="top">
                    {field.help}
                  </TooltipContent>
                </Tooltip>
              </div>
              <Input
                id={field.key}
                type="number"
                step={field.step}
                value={draft[field.key]}
                disabled={isPending}
                onChange={(event) => {
                  const nextValue = event.target.value;
                  setDraft((current) => ({
                    ...current,
                    [field.key]: nextValue,
                  }));
                }}
              />
            </div>
          ))}
        </div>
        <Button type="submit" disabled={isPending} className="self-start">
          {isPending ? "Detectando…" : "Detectar fuentes"}
        </Button>
      </form>
    </TooltipProvider>
  );
}
