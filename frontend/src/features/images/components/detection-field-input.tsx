import { HelpHint } from "@/components/ui/help-hint";
import type { DetectionField } from "../source-detection-fields";
import { DecimalInput } from "./decimal-input";

export function DetectionFieldInput({
  field,
  value,
  isPending,
  onValueChange,
}: Readonly<{
  field: DetectionField<string>;
  value: string;
  isPending: boolean;
  onValueChange: (value: string) => void;
}>) {
  return (
    <div className="flex flex-col gap-1 text-sm">
      <div className="flex items-center gap-1">
        <label htmlFor={field.key} className="text-muted-foreground">
          {field.label}
        </label>
        <HelpHint
          label={field.label}
          testId={`source-help-${field.key}`}
          glossaryId={field.glossaryId}
        >
          {field.help}
        </HelpHint>
      </div>
      <DecimalInput
        id={field.key}
        testId={`source-field-${field.key}`}
        step={field.step}
        value={value}
        disabled={isPending}
        onValueChange={onValueChange}
      />
    </div>
  );
}
