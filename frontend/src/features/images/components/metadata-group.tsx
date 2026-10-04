import { Copy } from "lucide-react";
import { toast } from "sonner";
import { HelpHint } from "@/components/ui/help-hint";

export type MetadataRow = {
  id: string;
  label: string;
  value: string;
  help: string;
  glossaryId?: string;
};

type MetadataGroupProps = {
  title: string;
  testId: string;
  rows: MetadataRow[];
};

function copyText(value: string) {
  const clipboard = navigator.clipboard;
  if (clipboard) {
    void clipboard.writeText(value).then(
      () => toast.success("Copiado"),
      () => {
        if (writeWithSelection(value)) {
          toast.success("Copiado");
        }
      },
    );
    return;
  }
  if (writeWithSelection(value)) {
    toast.success("Copiado");
  }
}

function writeWithSelection(value: string): boolean {
  const area = document.createElement("textarea");
  area.value = value;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.left = "-9999px";
  document.body.append(area);
  area.select();
  const copied = document.execCommand("copy");
  area.remove();
  return copied;
}

export function CopyableValue({
  label,
  value,
  testId,
}: Readonly<{ label: string; value: string; testId?: string }>) {
  return (
    <dd
      data-testid={testId}
      className="group/copy flex min-w-0 items-center gap-1 font-medium"
    >
      <button
        type="button"
        className="min-w-0 cursor-pointer truncate text-left underline-offset-2 hover:underline"
        onClick={() => copyText(value)}
      >
        {value}
      </button>
      <button
        type="button"
        className="shrink-0 cursor-pointer rounded-sm p-0.5 text-muted-foreground opacity-0 group-hover/copy:opacity-100 focus-visible:opacity-100"
        aria-label={`Copiar ${label}`}
        data-testid={testId ? `copy-${testId}` : undefined}
        onClick={() => copyText(value)}
      >
        <Copy className="size-3" />
      </button>
    </dd>
  );
}

export function MetadataGroup({
  title,
  testId,
  rows,
}: Readonly<MetadataGroupProps>) {
  if (rows.length === 0) {
    return null;
  }

  const grouped = rows.map((row) => `${row.label}: ${row.value}`).join("\n");

  return (
    <div data-testid={testId} className="mb-3">
      <h3 className="group/section sticky top-8 z-20 -mx-2 flex h-8 items-center bg-sidebar px-2 text-xs font-medium text-foreground">
        <button
          type="button"
          className="flex h-8 min-w-0 flex-1 cursor-pointer items-center gap-1 text-left"
          aria-label={`Copiar ${title}`}
          data-testid={`copy-group-${testId}`}
          onClick={(event) => {
            event.stopPropagation();
            copyText(grouped);
          }}
        >
          <span className="underline-offset-2 group-hover/section:underline">
            {title}
          </span>
          <Copy className="size-3 shrink-0 text-muted-foreground opacity-0 group-hover/section:opacity-100" />
        </button>
        <HelpHint
          label={`Copiar ${title}`}
          testId={`help-copy-${testId}`}
          glossaryId="copiar-dato"
        >
          El título copia todas las líneas del grupo. Cada valor copia solo ese
          dato.
        </HelpHint>
      </h3>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
        {rows.map((row) => (
          <div key={row.id} className="contents">
            <dt className="flex items-center gap-1 text-muted-foreground">
              {row.label}
              <HelpHint
                label={row.label}
                testId={`help-${row.id}`}
                glossaryId={row.glossaryId}
              >
                {row.help}
              </HelpHint>
            </dt>
            <CopyableValue
              label={row.label}
              value={row.value}
              testId={`meta-${row.id}`}
            />
          </div>
        ))}
      </dl>
    </div>
  );
}
