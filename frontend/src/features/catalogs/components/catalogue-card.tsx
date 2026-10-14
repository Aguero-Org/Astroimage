import { ChevronDown, ExternalLink } from "lucide-react";
import { Fragment, type ReactNode } from "react";
import type { CatalogRecommendationItemSchema } from "@/api/generated/model";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  adsUrlForBibcode,
  catalogueCrossmatchNote,
  catalogueMatchLabel,
  catalogueName,
  catalogueReason,
  catalogueSeparation,
  doiUrlFor,
  shortenText,
} from "../catalog-recommendations";

type CatalogueCardProps = {
  item: CatalogRecommendationItemSchema;
  radiusArcsec?: number;
};

export function CatalogueCard({
  item,
  radiusArcsec,
}: Readonly<CatalogueCardProps>) {
  const title = catalogueName(item);
  const authors = item.catalogue_authors?.trim() || undefined;
  const description = shortenText(item.catalogue_description, 220);
  const reason = catalogueReason(item);
  const crossmatch = catalogueCrossmatchNote(item);
  const separation = catalogueSeparation(item);
  const links = buildLinks(item);
  const rows = buildRows(item, radiusArcsec, separation);

  return (
    <Collapsible asChild>
      <article
        data-testid="catalogue-card"
        className="rounded-lg border border-sidebar-border bg-sidebar-accent/30"
      >
        <CollapsibleTrigger asChild>
          <button
            type="button"
            data-testid="catalogue-card-toggle"
            className="group/row flex w-full items-start gap-2 p-2 text-left"
          >
            <ChevronDown className="mt-0.5 size-4 shrink-0 text-muted-foreground transition-transform group-data-[state=open]/row:rotate-180" />
            <span className="min-w-0 flex-1">
              <span
                data-testid="catalogue-card-name"
                className="block text-sm leading-snug font-semibold"
              >
                {title}
              </span>
              {authors ? (
                <span
                  data-testid="catalogue-card-authors"
                  className="mt-0.5 block truncate text-xs text-muted-foreground"
                >
                  {authors}
                </span>
              ) : null}
              <span className="mt-1 flex flex-wrap items-center gap-2">
                <span
                  data-testid="catalogue-card-match"
                  className="rounded-full border border-sidebar-border px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-muted-foreground uppercase"
                >
                  {catalogueMatchLabel(item)}
                </span>
                {separation ? (
                  <span
                    data-testid="catalogue-card-separation"
                    className="text-xs text-muted-foreground"
                  >
                    Separación {separation}
                  </span>
                ) : null}
              </span>
              <span
                data-testid="catalogue-card-reason"
                className="mt-1 block text-xs text-muted-foreground"
              >
                {reason.headline}
              </span>
              {description ? (
                <span
                  data-testid="catalogue-card-description"
                  className="mt-1 line-clamp-2 block text-[11px] leading-snug text-muted-foreground"
                >
                  {description}
                </span>
              ) : null}
            </span>
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent data-testid="catalogue-card-detail">
          <div className="flex flex-col gap-3 border-t border-sidebar-border p-2">
            {reason.detail || crossmatch ? (
              <DetailSection title="Por qué se recomienda">
                {reason.detail ? (
                  <p className="text-xs text-muted-foreground">
                    {reason.detail}
                  </p>
                ) : null}
                {crossmatch ? (
                  <p
                    data-testid="catalogue-card-crossmatch"
                    className="text-xs text-muted-foreground"
                  >
                    {crossmatch}
                  </p>
                ) : null}
              </DetailSection>
            ) : null}
            {rows.length > 0 ? (
              <DetailSection title="Datos del catálogo">
                <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
                  {rows.map((row) => (
                    <Fragment key={row.label}>
                      <dt className="text-muted-foreground">{row.label}</dt>
                      <dd className="min-w-0 break-words">{row.value}</dd>
                    </Fragment>
                  ))}
                </dl>
              </DetailSection>
            ) : null}
            {links.length > 0 ? (
              <DetailSection title="Vínculos">
                <ul className="flex flex-col gap-1">
                  {links.map((link) => (
                    <li key={link.id}>
                      <a
                        data-testid={`catalogue-link-${link.id}`}
                        href={link.href}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-primary underline-offset-2 hover:underline"
                      >
                        {link.label}
                        <ExternalLink className="size-3" />
                      </a>
                    </li>
                  ))}
                </ul>
              </DetailSection>
            ) : null}
          </div>
        </CollapsibleContent>
      </article>
    </Collapsible>
  );
}

function DetailSection({
  title,
  children,
}: Readonly<{ title: string; children: ReactNode }>) {
  return (
    <section className="flex flex-col gap-1">
      <h4 className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">
        {title}
      </h4>
      {children}
    </section>
  );
}

type DetailRow = {
  label: string;
  value: string;
};

function buildRows(
  item: CatalogRecommendationItemSchema,
  radiusArcsec: number | undefined,
  separation: string | undefined,
): DetailRow[] {
  const rows: DetailRow[] = [{ label: "VizieR", value: item.catalogue_id }];
  if (item.catalogue_bibcode?.trim()) {
    rows.push({ label: "Bibcode", value: item.catalogue_bibcode.trim() });
  }
  if (item.catalogue_doi?.trim()) {
    rows.push({ label: "DOI", value: item.catalogue_doi.trim() });
  }
  if (item.object_identifier?.trim()) {
    const columns = item.identifier_columns?.trim();
    rows.push({
      label: "Objeto",
      value: columns
        ? `${item.object_identifier.trim()} (${columns})`
        : item.object_identifier.trim(),
    });
  }
  if (separation) {
    rows.push({ label: "Separación", value: separation });
  }
  if (radiusArcsec !== undefined) {
    rows.push({ label: "Radio de búsqueda", value: `${radiusArcsec}″` });
  }
  if (item.catalogue_keywords?.trim()) {
    rows.push({
      label: "Palabras clave",
      value: item.catalogue_keywords.trim(),
    });
  }
  return rows;
}

type CatalogueLink = {
  id: string;
  label: string;
  href: string;
};

function buildLinks(item: CatalogRecommendationItemSchema): CatalogueLink[] {
  const links: CatalogueLink[] = [];
  pushLink(links, "vizier", "Ver en VizieR", item.vizier_url);
  pushLink(links, "readme", "ReadMe del catálogo", item.readme_url);
  pushLink(
    links,
    "ads",
    "Artículo en ADS",
    item.paper_ads_url ??
      (item.paper_bibcode ? adsUrlForBibcode(item.paper_bibcode) : undefined),
  );
  pushLink(
    links,
    "doi",
    "Artículo por DOI",
    item.paper_doi_url ??
      (item.paper_doi ? doiUrlFor(item.paper_doi) : undefined),
  );
  return links;
}

function pushLink(
  links: CatalogueLink[],
  id: string,
  label: string,
  raw: string | null | undefined,
) {
  const href = safeUrl(raw);
  if (href) {
    links.push({ id, label, href });
  }
}

function safeUrl(raw: string | null | undefined): string | undefined {
  const value = raw?.trim();
  if (!value) {
    return undefined;
  }
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:"
      ? url.toString()
      : undefined;
  } catch {
    return undefined;
  }
}
