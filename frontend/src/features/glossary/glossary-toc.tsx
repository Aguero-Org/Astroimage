import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import type { GlossaryEntry } from "./entries";

export type GlossarySection = {
  id: string;
  title: string;
  entries: GlossaryEntry[];
};

type GlossaryTocProps = {
  sections: readonly GlossarySection[];
  activeId: string;
};

function keepActiveVisible(nav: HTMLElement, activeId: string) {
  if (nav.scrollHeight <= nav.clientHeight) {
    return;
  }
  const link = nav.querySelector<HTMLElement>(`[data-entry-id="${activeId}"]`);
  if (!link) {
    return;
  }
  const navRect = nav.getBoundingClientRect();
  const linkRect = link.getBoundingClientRect();
  const linkCenter = linkRect.top + linkRect.height / 2;
  const navCenter = navRect.top + navRect.height / 2;
  nav.scrollTop += linkCenter - navCenter;
}

export function GlossaryToc({
  sections,
  activeId,
}: Readonly<GlossaryTocProps>) {
  const navRef = useRef<HTMLElement>(null);
  const activeSectionId = sections.find((section) =>
    section.entries.some((entry) => entry.id === activeId),
  )?.id;

  useEffect(() => {
    const nav = navRef.current;
    if (nav && activeId.length > 0) {
      keepActiveVisible(nav, activeId);
    }
  }, [activeId]);

  return (
    <nav
      ref={navRef}
      data-testid="glossary-toc"
      className="lg:sticky lg:top-[var(--glossary-scroll-pad,12rem)] lg:max-h-[calc(100svh-var(--glossary-scroll-pad,12rem))] lg:overflow-y-auto"
    >
      <p className="mb-3 text-xs font-medium tracking-wide text-muted-foreground uppercase">
        En esta página
      </p>
      <ol className="flex flex-wrap gap-x-4 gap-y-1 text-sm lg:flex-col lg:flex-nowrap lg:gap-0">
        {sections.map((section) => (
          <li key={section.id} className="lg:mt-3 lg:first:mt-0">
            <a
              href={`#${section.id}`}
              data-active={activeSectionId === section.id || undefined}
              className={cn(
                "font-medium text-foreground hover:underline",
                activeSectionId === section.id &&
                  "underline decoration-2 underline-offset-4",
              )}
            >
              {section.title}
            </a>
            <ol className="mt-1 hidden lg:block">
              {section.entries.map((entry) => (
                <li key={entry.id}>
                  <a
                    href={`#${entry.id}`}
                    data-entry-id={entry.id}
                    data-active={activeId === entry.id || undefined}
                    className={cn(
                      "block border-l py-0.5 pl-3 text-muted-foreground hover:text-foreground hover:underline",
                      activeId === entry.id &&
                        "border-foreground font-bold text-foreground",
                    )}
                  >
                    {entry.name}
                  </a>
                </li>
              ))}
            </ol>
          </li>
        ))}
      </ol>
    </nav>
  );
}
