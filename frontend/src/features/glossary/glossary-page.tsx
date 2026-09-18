import { useLocation } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import {
  filterGlossaryEntries,
  GLOSSARY_ENTRIES,
  GLOSSARY_GROUPS,
} from "./entries";

export function GlossaryPage() {
  const [query, setQuery] = useState("");
  const location = useLocation();
  const filtered = useMemo(
    () => filterGlossaryEntries(GLOSSARY_ENTRIES, query),
    [query],
  );

  useEffect(() => {
    const id = location.hash.replace("#", "");
    if (id.length === 0) {
      return;
    }
    document.getElementById(id)?.scrollIntoView({ block: "start" });
  }, [location.hash]);

  return (
    <main
      data-testid="glossary-page"
      className="mx-auto flex min-h-svh w-full max-w-3xl flex-col gap-6 px-4 py-20 sm:px-6"
    >
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">Glosario</h1>
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
      </div>
      {GLOSSARY_GROUPS.map((group) => {
        const entries = filtered.filter((entry) => entry.group === group.id);
        if (entries.length === 0) {
          return null;
        }
        return (
          <section
            key={group.id}
            data-testid={`glossary-group-${group.id}`}
            className="flex flex-col gap-4"
          >
            <h2 className="text-lg font-medium">{group.title}</h2>
            {entries.map((entry) => (
              <article
                key={entry.id}
                id={entry.id}
                data-testid={`glossary-entry-${entry.id}`}
                className="scroll-mt-24 rounded-xl border border-border bg-card p-4 text-card-foreground"
              >
                <h3 className="text-base font-semibold">{entry.name}</h3>
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
