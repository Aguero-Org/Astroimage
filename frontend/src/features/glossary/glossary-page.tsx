import { useLocation } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { readLastImageRecord } from "@/features/images/last-record";
import { useScrollSpy, useStickyStackHeight } from "@/hooks/use-scroll-spy";
import {
  filterGlossaryEntries,
  GLOSSARY_ENTRIES,
  GLOSSARY_GROUPS,
} from "./entries";
import { GlossaryArticle } from "./glossary-article";
import { GlossaryHeader } from "./glossary-header";
import { GlossaryToc } from "./glossary-toc";

const STICKY_STACK_IDS = ["navbar", "glossary-header"] as const;

export function GlossaryPage() {
  const [query, setQuery] = useState("");
  const location = useLocation();
  const lastRecordId = readLastImageRecord();
  const hashId = location.hash.replace("#", "");
  const stickyOffset = useStickyStackHeight(STICKY_STACK_IDS);
  const filtered = useMemo(
    () => filterGlossaryEntries(GLOSSARY_ENTRIES, query),
    [query],
  );
  const sections = useMemo(
    () =>
      GLOSSARY_GROUPS.map((group) => ({
        ...group,
        entries: filtered.filter((entry) => entry.group === group.id),
      })).filter((group) => group.entries.length > 0),
    [filtered],
  );
  const entryIds = useMemo(
    () =>
      sections.flatMap((section) => section.entries.map((entry) => entry.id)),
    [sections],
  );
  const activeId = useScrollSpy(entryIds, {
    offsetPx: stickyOffset,
    fallbackId: hashId,
  });

  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty("--glossary-scroll-pad", `${stickyOffset}px`);
    return () => {
      root.style.removeProperty("--glossary-scroll-pad");
    };
  }, [stickyOffset]);

  useEffect(() => {
    document.getElementById(hashId)?.scrollIntoView({ block: "start" });
  }, [hashId]);

  return (
    <main
      data-testid="glossary-page"
      className="mx-auto w-full max-w-6xl px-4 pt-8 pb-[50vh] sm:px-6 lg:px-8"
    >
      <GlossaryHeader
        query={query}
        lastRecordId={lastRecordId}
        onQueryChange={setQuery}
      />
      <div className="mt-12 grid gap-12 lg:grid-cols-[13rem_minmax(0,42rem)] lg:items-start">
        <GlossaryToc sections={sections} activeId={activeId} />
        <div className="min-w-0">
          {sections.map((section) => (
            <section
              key={section.id}
              id={section.id}
              data-testid={`glossary-group-${section.id}`}
              className="border-t border-border pt-12 first:border-t-0 first:pt-0"
            >
              <h2 className="text-2xl font-semibold tracking-tight">
                {section.title}
              </h2>
              {section.entries.map((entry) => (
                <GlossaryArticle
                  key={entry.id}
                  entry={entry}
                  isActive={activeId === entry.id}
                />
              ))}
            </section>
          ))}
          {filtered.length === 0 && (
            <p data-testid="glossary-empty" className="text-muted-foreground">
              No hay conceptos que coincidan.
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
