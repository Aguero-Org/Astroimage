import { HelpHint } from "@/components/ui/help-hint";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CUSTOM_PRESET_ID, type NamedPreset } from "../named-preset";

type NamedPresetFieldProps<T> = {
  label: string;
  testId: string;
  presets: readonly NamedPreset<T>[];
  value: string;
  lastNamedId: string;
  disabled: boolean;
  onSelect: (preset: NamedPreset<T>) => void;
};

export function NamedPresetField<T>({
  label,
  testId,
  presets,
  value,
  lastNamedId,
  disabled,
  onSelect,
}: Readonly<NamedPresetFieldProps<T>>) {
  const selected =
    presets.find((preset) => preset.id === value) ??
    presets.find((preset) => preset.id === lastNamedId);
  const triggerLabel =
    value === CUSTOM_PRESET_ID
      ? "Personalizado"
      : (selected?.label ?? "Personalizado");
  const outcome = selected?.outcome;
  const hint = selected?.hint;

  return (
    <fieldset className="flex flex-col gap-1 text-sm">
      <legend className="mb-1 flex items-center gap-1">
        <span className="text-muted-foreground">{label}</span>
        {hint ? (
          <HelpHint label={label} testId={`${testId}-help`}>
            {hint}
          </HelpHint>
        ) : null}
      </legend>
      <Select
        value={value}
        disabled={disabled}
        onValueChange={(nextId) => {
          const preset = presets.find((item) => item.id === nextId);
          if (preset) {
            onSelect(preset);
          }
        }}
      >
        <SelectTrigger id={testId} data-testid={testId}>
          <SelectValue>{triggerLabel}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={CUSTOM_PRESET_ID} data-testid={`${testId}-custom`}>
            Personalizado
          </SelectItem>
          {presets.map((preset) => (
            <SelectItem
              key={preset.id}
              value={preset.id}
              data-testid={`${testId}-${preset.id}`}
            >
              <span className="flex flex-col gap-0.5 py-0.5">
                <span>{preset.label}</span>
                <span className="text-muted-foreground text-xs leading-snug">
                  {preset.outcome}
                </span>
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {outcome ? (
        <p
          data-testid={`${testId}-outcome`}
          className="text-muted-foreground text-xs leading-snug"
        >
          {outcome}
        </p>
      ) : null}
    </fieldset>
  );
}
