import { Link2 } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { type GlossaryEntry, glossaryPath } from "./entries";

type GlossaryArticleProps = {
  entry: GlossaryEntry;
  isActive: boolean;
};

export function GlossaryArticle({
  entry,
  isActive,
}: Readonly<GlossaryArticleProps>) {
  return (
    <article
      id={entry.id}
      data-testid={`glossary-entry-${entry.id}`}
      data-active={isActive ? "true" : undefined}
      className="py-8"
    >
      <div className="flex items-baseline gap-2">
        <h3 className="text-xl font-semibold tracking-tight">
          <a href={`#${entry.id}`} className="hover:underline">
            {entry.name}
          </a>
        </h3>
        <CopyEntryLink entryId={entry.id} />
      </div>
      <p className="mt-4 text-base leading-8">{entry.what}</p>
      <p className="mt-4 text-base leading-8">
        {entry.inApp} Lo ves en {entry.where}.
      </p>
    </article>
  );
}

function CopyEntryLink({ entryId }: Readonly<{ entryId: string }>) {
  const [copied, setCopied] = useState(false);

  async function copyLink() {
    const url = `${window.location.origin}${glossaryPath(entryId)}`;
    await navigator.clipboard.writeText(url);
    setCopied(true);
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      data-testid={`glossary-copy-${entryId}`}
      aria-label={copied ? "Enlace copiado" : `Copiar enlace a ${entryId}`}
      className="size-7 shrink-0 text-muted-foreground hover:text-foreground"
      onClick={() => {
        void copyLink();
      }}
    >
      <Link2 className="size-3.5" />
    </Button>
  );
}
