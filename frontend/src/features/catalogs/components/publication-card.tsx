import { FileText } from "lucide-react";
import { HelpHint } from "@/components/ui/help-hint";
import type { CatalogPublication } from "../catalog-recommendations";
import { publicationHeading, shortenText } from "../catalog-recommendations";

type PublicationCardProps = {
  publication: CatalogPublication;
};

export function PublicationCard({
  publication,
}: Readonly<PublicationCardProps>) {
  const href = publication.doiUrl ?? publication.adsUrl;
  const title = publicationHeading(publication);
  const abstract = shortenText(publication.abstract, 220);
  const identifier = publication.bibcode ?? publication.doi;
  const showIdentifier = identifier !== undefined && identifier !== title;

  return (
    <article
      data-testid="publication-card"
      className="group relative rounded-lg border border-sidebar-border bg-sidebar-accent/30 p-2 hover:bg-sidebar-accent/60"
    >
      {href ? (
        <a
          data-testid="publication-link"
          href={href}
          target="_blank"
          rel="noreferrer"
          aria-label={title}
          className="absolute inset-0 rounded-lg"
        >
          <span className="sr-only">{title}</span>
        </a>
      ) : null}
      <div className="pointer-events-none relative z-10 flex items-start gap-2">
        <FileText className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1">
            <p
              data-testid="publication-label"
              className="text-sm leading-snug font-medium group-hover:underline"
            >
              {title}
            </p>
            <span className="pointer-events-auto">
              <HelpHint
                label="Publicación"
                testId="help-publication"
                glossaryId="referencia-publicacion"
              >
                Título del artículo y un extracto del abstract. La tarjeta abre
                el trabajo en ADS o por su DOI.
              </HelpHint>
            </span>
          </div>
          <p
            data-testid="publication-kind"
            className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground"
          >
            {publication.kind === "catalogue-paper"
              ? "Artículo del catálogo"
              : "Referencia citada en el ReadMe"}
            <span className="pointer-events-auto">
              <HelpHint
                label="Publicación asociada"
                testId="help-publication-kind"
                glossaryId="publicacion-vizier"
              >
                Artículo que describe el catálogo o que su documentación cita.
                Pasar el cursor y abrir la tarjeta lleva a ADS o al DOI.
              </HelpHint>
            </span>
          </p>
          {abstract ? (
            <p
              data-testid="publication-abstract"
              className="mt-1 line-clamp-3 text-xs leading-snug text-muted-foreground"
            >
              {abstract}
            </p>
          ) : null}
          {showIdentifier ? (
            <p
              data-testid="publication-identifier"
              className="mt-0.5 truncate text-xs text-muted-foreground"
            >
              {identifier}
            </p>
          ) : null}
        </div>
      </div>
    </article>
  );
}
