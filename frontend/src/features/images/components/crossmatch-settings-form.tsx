import { useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { Label } from "@/components/ui/label";
import {
  type CrossmatchDraft,
  type CrossmatchParams,
  crossmatchToDraft,
  parseCrossmatchDraft,
} from "../crossmatch";
import { DecimalInput } from "./decimal-input";

type CrossmatchField = {
  key: keyof CrossmatchDraft;
  label: string;
  testId: string;
  help: string;
  glossaryId: string;
  step: string;
};

const GAIA_FIELDS: CrossmatchField[] = [
  {
    key: "gaiaRadius",
    label: "Radio de cruce",
    testId: "crossmatch-gaia-radius",
    help: "Distancia máxima, en segundos de arco, entre una detección y una fuente Gaia para considerarlas la misma.",
    glossaryId: "radio-cruce",
    step: "0.5",
  },
  {
    key: "gaiaPower",
    label: "Exponente de probabilidad",
    testId: "crossmatch-gaia-power",
    help: "Controla cuánto cae la probabilidad a medida que la fuente se aleja del centro del radio. Un valor más alto castiga más las separaciones grandes.",
    glossaryId: "exponente-probabilidad",
    step: "0.1",
  },
];

const SIMBAD_FIELDS: CrossmatchField[] = [
  {
    key: "simbadRadius",
    label: "Radio de cruce",
    testId: "crossmatch-simbad-radius",
    help: "Distancia máxima, en segundos de arco, entre una detección y un objeto SIMBAD para considerarlas la misma fuente.",
    glossaryId: "radio-cruce",
    step: "0.5",
  },
  {
    key: "simbadPower",
    label: "Exponente de probabilidad",
    testId: "crossmatch-simbad-power",
    help: "Controla cuánto cae la probabilidad a medida que el objeto se aleja del centro del radio. Un valor más alto castiga más las separaciones grandes.",
    glossaryId: "exponente-probabilidad",
    step: "0.1",
  },
];

export function CrossmatchSettingsForm({
  params,
  onSubmit,
}: Readonly<{
  params: CrossmatchParams;
  onSubmit: (params: CrossmatchParams) => void;
}>) {
  const [draft, setDraft] = useState(() => crossmatchToDraft(params));
  const parsed = parseCrossmatchDraft(draft);

  function update(key: keyof CrossmatchDraft, value: string) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  return (
    <form
      data-testid="crossmatch-settings-form"
      className="mt-3 flex flex-col gap-3 rounded-md border border-border p-3"
      onSubmit={(event) => {
        event.preventDefault();
        if (parsed !== null) {
          onSubmit(parsed);
        }
      }}
    >
      <div className="flex items-center gap-1">
        <h3 className="text-sm font-semibold text-foreground">
          Parámetros del cruce
        </h3>
        <HelpHint
          label="Parámetros del cruce"
          testId="crossmatch-help"
          glossaryId="radio-cruce"
        >
          Definen qué separación cuenta como coincidencia y cómo baja la
          probabilidad al alejarse.
        </HelpHint>
      </div>
      <CrossmatchFieldGroup
        title="Gaia"
        fields={GAIA_FIELDS}
        draft={draft}
        onChange={update}
      />
      <CrossmatchFieldGroup
        title="SIMBAD"
        fields={SIMBAD_FIELDS}
        draft={draft}
        onChange={update}
      />
      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="submit"
          data-testid="crossmatch-apply"
          disabled={parsed === null}
        >
          Aplicar
        </Button>
        {parsed === null ? (
          <p
            data-testid="crossmatch-error"
            className="text-xs text-destructive"
          >
            Revisá los valores: el radio va de 0 a 3600 y el exponente es 0,1 o
            más.
          </p>
        ) : null}
      </div>
    </form>
  );
}

function CrossmatchFieldGroup({
  title,
  fields,
  draft,
  onChange,
}: Readonly<{
  title: string;
  fields: CrossmatchField[];
  draft: CrossmatchDraft;
  onChange: (key: keyof CrossmatchDraft, value: string) => void;
}>) {
  return (
    <section className="flex flex-col gap-2">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {fields.map((field) => (
          <div key={field.key} className="flex flex-col gap-1 text-sm">
            <div className="flex items-center gap-1">
              <Label
                htmlFor={`crossmatch-${field.key}`}
                className="font-normal leading-normal text-muted-foreground"
              >
                {field.label}
              </Label>
              <HelpHint
                label={field.label}
                testId={`crossmatch-help-${field.testId}`}
                glossaryId={field.glossaryId}
              >
                {field.help}
              </HelpHint>
            </div>
            <DecimalInput
              id={`crossmatch-${field.key}`}
              testId={field.testId}
              step={field.step}
              value={draft[field.key]}
              onValueChange={(value) => onChange(field.key, value)}
            />
          </div>
        ))}
      </div>
    </section>
  );
}
