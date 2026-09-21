import { Link, useLocation } from "@tanstack/react-router";
import { Link2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { readLastImageRecord } from "@/features/images/last-record";
import { cn } from "@/lib/utils";
import {
  filterGlossaryEntries,
  GLOSSARY_ENTRIES,
  GLOSSARY_GROUPS,
  glossaryPath,
} from "./entries";

export function GlossaryPage() {
  const [query, setQuery] = useState("");
  const location = useLocation();
  const lastRecordId = readLastImageRecord();
  const activeId = location.hash.replace("#", "");
  const filtered = useMemo(
    () => filterGlossaryEntries(GLOSSARY_ENTRIES, query),
    [query],
  );

  useEffect(() => {
    if (activeId.length === 0) {
      return;
    }
    document.getElementById(activeId)?.scrollIntoView({ block: "start" });
  }, [activeId]);

  return (
    <main
      data-testid="glossary-page"
      className="mx-auto flex min-h-svh w-full max-w-3xl flex-col gap-6 px-4 py-20 sm:px-6"
    >
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">Glosario</h1>
          {lastRecordId ? (
            <Link
              to="/image/$recordId"
              params={{ recordId: lastRecordId }}
              data-testid="glossary-back-to-viewer"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Volver al visor
            </Link>
          ) : null}
        </div>
        <p className="text-sm text-muted-foreground">
          Conceptos que usa Astroimage, en el idioma de la pantalla. El tooltip
          del visor es la versión corta; acá está el detalle.
        </p>
        <Input
          type="search"
          data-testid="glossary-search"
          aria-label="Buscar en el glosario"
          placeholder="Buscar un concepto…"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
          }}
        />
        <nav
          data-testid="glossary-toc"
          className="flex flex-wrap gap-x-4 gap-y-1 text-sm"
        >
          {GLOSSARY_GROUPS.map((group) => (
            <a
              key={group.id}
              href={`#${group.id}`}
              className="text-muted-foreground hover:text-foreground"
            >
              {group.title}
            </a>
          ))}
        </nav>
      </div>
      {GLOSSARY_GROUPS.map((group) => {
        const entries = filtered.filter((entry) => entry.group === group.id);
        if (entries.length === 0) {
          return null;
        }
        return (
          <section
            key={group.id}
            id={group.id}
            data-testid={`glossary-group-${group.id}`}
            className="flex scroll-mt-24 flex-col gap-4"
          >
            <h2 className="text-lg font-medium">{group.title}</h2>
            {entries.map((entry) => (
              <article
                key={entry.id}
                id={entry.id}
                data-testid={`glossary-entry-${entry.id}`}
                className={cn(
                  "scroll-mt-24 rounded-xl border border-border bg-card p-4 text-card-foreground",
                  activeId === entry.id && "ring-2 ring-ring",
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-base font-semibold">{entry.name}</h3>
                  <CopyEntryLink entryId={entry.id} />
                </div>
                <p className="mt-2 text-sm">{entry.what}</p>
                <p className="mt-2 text-sm text-muted-foreground">
                  En Astroimage: {entry.inApp}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Dónde: {entry.where}
                </p>
              </article>
            ))}
          </section>
        );
      })}
      {filtered.length === 0 ? (
        <p
          data-testid="glossary-empty"
          className="text-sm text-muted-foreground"
        >
          No hay conceptos que coincidan.
        </p>
      ) : null}
    </main>
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
      className="size-8 shrink-0"
      onClick={() => {
        void copyLink();
      }}
    >
      <Link2 className="size-4" />
    </Button>
  );
}
