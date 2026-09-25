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

export function GlossaryToc({
  sections,
  activeId,
}: Readonly<GlossaryTocProps>) {
  return (
    <nav
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
              className="font-medium text-foreground hover:underline"
            >
              {section.title}
            </a>
            <ol className="mt-1 hidden lg:block">
              {section.entries.map((entry) => (
                <li key={entry.id}>
                  <a
                    href={`#${entry.id}`}
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
