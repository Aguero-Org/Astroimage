import type { ReactNode } from "react";
import { HelpHint } from "@/components/ui/help-hint";

export function RenderField({
  label,
  testId,
  help,
  glossaryId,
  children,
}: Readonly<{
  label: string;
  testId: string;
  help: string;
  glossaryId?: string;
  children: ReactNode;
}>) {
  return (
    <fieldset className="flex flex-col gap-1 text-sm">
      <legend className="mb-1 flex items-center gap-1">
        <span className="text-muted-foreground">{label}</span>
        <HelpHint
          label={label}
          testId={`render-help-${testId.replace("render-", "")}`}
          glossaryId={glossaryId}
        >
          {help}
        </HelpHint>
      </legend>
      {children}
    </fieldset>
  );
}
