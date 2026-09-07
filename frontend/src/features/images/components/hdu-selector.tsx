import type { FitsHduDetailSchema } from "@/api/generated/model";
import { HelpHint } from "@/components/ui/help-hint";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type HduSelectorProps = {
  images: FitsHduDetailSchema[];
  value: number | null;
  onChange: (hdu: number) => void;
};

function hduLabel(hdu: FitsHduDetailSchema): string {
  const parts = [String(hdu.index)];
  if (hdu.extname) {
    parts.push(hdu.extname);
  }
  if (hdu.kind) {
    parts.push(hdu.kind);
  }
  return parts.join(" · ");
}

export function HduSelector({
  images,
  value,
  onChange,
}: Readonly<HduSelectorProps>) {
  if (images.length <= 1) {
    return null;
  }

  const selected = value ?? images[0]?.index;

  return (
    <div className="flex flex-col gap-1 px-4 pb-3">
      <div className="flex items-center gap-1 text-xs text-muted-foreground">
        HDU
        <HelpHint label="HDU" testId="help-hdu">
          Cada FITS puede traer varios planos de imagen. Render, detección e
          histograma usan el mismo HDU.
        </HelpHint>
      </div>
      <Select
        value={selected === undefined ? undefined : String(selected)}
        onValueChange={(next) => {
          onChange(Number(next));
        }}
      >
        <SelectTrigger data-testid="hdu-selector" className="h-8">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {images.map((hdu) => (
            <SelectItem
              key={hdu.index}
              value={String(hdu.index)}
              data-testid={`hdu-option-${hdu.index}`}
            >
              {hduLabel(hdu)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
