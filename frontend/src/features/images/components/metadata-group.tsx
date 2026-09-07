import { HelpHint } from "@/components/ui/help-hint";

export type MetadataRow = {
  id: string;
  label: string;
  value: string;
  help: string;
};

type MetadataGroupProps = {
  title: string;
  testId: string;
  rows: MetadataRow[];
};

export function MetadataGroup({
  title,
  testId,
  rows,
}: Readonly<MetadataGroupProps>) {
  if (rows.length === 0) {
    return null;
  }

  return (
    <div data-testid={testId} className="mb-3">
      <h3 className="mb-1 text-xs font-medium text-foreground">{title}</h3>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
        {rows.map((row) => (
          <div key={row.id} className="contents">
            <dt className="flex items-center gap-1 text-muted-foreground">
              {row.label}
              <HelpHint label={row.label} testId={`help-${row.id}`}>
                {row.help}
              </HelpHint>
            </dt>
            <dd data-testid={`meta-${row.id}`} className="truncate font-medium">
              {row.value}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
