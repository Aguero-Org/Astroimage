import { FileText } from "lucide-react";
import { HelpHint } from "@/components/ui/help-hint";
import type { CatalogPublication } from "../catalog-recommendations";
import { publicationLabel } from "../catalog-recommendations";

type PublicationCardProps = {
  publication: CatalogPublication;
};

export function PublicationCard({
  publication,
}: Readonly<PublicationCardProps>) {
  const href = publication.doiUrl ?? publication.adsUrl;
  const isCataloguePaper = publication.kind === "catalogue-paper";

  return (
    <article
      data-testid="publication-card"
      className="rounded-lg border border-sidebar-border bg-sidebar-accent/30 p-2"
    >
      <div className="flex items-start gap-2">
        <FileText className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1">
            <p
              data-testid="publication-label"
              className="truncate text-sm font-medium"
            >
              {publicationLabel(publication)}
            </p>
            <HelpHint
              label="Publicación"
              testId="help-publication"
              glossaryId="referencia-publicacion"
            >
              Referencia bibliográfica del artículo asociado al catálogo,
              identificada por su bibcode o DOI.
            </HelpHint>
          </div>
          <p
            data-testid="publication-kind"
            className="mt-0.5 text-xs text-muted-foreground"
          >
            {isCataloguePaper
              ? "Artículo del catálogo"
              : "Referencia citada en el ReadMe"}
          </p>
          {publication.catalogueNames.length > 0 ? (
            <p
              data-testid="publication-catalogues"
              className="mt-0.5 text-xs text-muted-foreground"
            >
              {isCataloguePaper ? "Artículo de " : "Citada por "}
              {publication.catalogueNames.join(", ")}
            </p>
          ) : null}
          {href ? (
            <a
              data-testid="publication-link"
              href={href}
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-flex items-center gap-1 text-xs text-primary underline-offset-2 hover:underline"
            >
              {publication.doiUrl ? "Abrir el paper" : "Ficha en ADS"}
            </a>
          ) : null}
        </div>
      </div>
    </article>
  );
}
