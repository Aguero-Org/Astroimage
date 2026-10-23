import type {
  CatalogRecommendationItemSchema,
  CatalogRecommendationResponse,
} from "@/api/generated/model";
import type { CatalogPublication } from "../catalog-recommendations";
import { CatalogueCard } from "./catalogue-card";
import { PublicationCard } from "./publication-card";
import {
  RecommendationError,
  RecommendationInfo,
  RecommendationLoading,
} from "./recommendation-states";

type RecommendationContentProps = {
  enabled: boolean;
  isError: boolean;
  isLoading: boolean;
  result: CatalogRecommendationResponse | undefined;
  tab: "catalogs" | "papers";
  items: CatalogRecommendationItemSchema[];
  matches: CatalogRecommendationItemSchema[];
  publications: CatalogPublication[];
  papers: CatalogPublication[];
  errorMessage: string;
  onRetry: () => void;
};

export function RecommendationContent({
  enabled,
  isError,
  isLoading,
  result,
  tab,
  items,
  matches,
  publications,
  papers,
  errorMessage,
  onRetry,
}: Readonly<RecommendationContentProps>) {
  if (!enabled) {
    return (
      <RecommendationInfo testId="catalogs-info">
        Las recomendaciones aparecerán cuando termine el análisis de Gaia.
      </RecommendationInfo>
    );
  }
  if (isError) {
    return <RecommendationError message={errorMessage} onRetry={onRetry} />;
  }
  if (isLoading) {
    return <RecommendationLoading />;
  }
  if (!result) {
    return (
      <RecommendationInfo testId="catalogs-info">
        Todavía no hay recomendaciones para esta imagen.
      </RecommendationInfo>
    );
  }
  if (result.error) {
    return <RecommendationError message={result.error} onRetry={onRetry} />;
  }
  if (result.wcs_present === false) {
    return (
      <RecommendationInfo testId="catalogs-info">
        Esta imagen no tiene información de posición (WCS), así que no se puede
        ubicar su región en el cielo para buscar catálogos.
      </RecommendationInfo>
    );
  }
  if (result.queried === false) {
    return (
      <RecommendationInfo testId="catalogs-info">
        No se pudo consultar VizieR para esta región del cielo.
      </RecommendationInfo>
    );
  }
  if (tab === "catalogs") {
    return (
      <CatalogList
        items={items}
        matches={matches}
        radiusArcsec={result.radius_arcsec}
      />
    );
  }
  if (publications.length === 0) {
    return (
      <RecommendationInfo testId="papers-empty">
        {result.include_papers === false
          ? "Las publicaciones no se incluyeron en esta consulta."
          : "No se encontraron publicaciones asociadas a estos catálogos."}
      </RecommendationInfo>
    );
  }
  if (papers.length === 0) {
    return (
      <RecommendationInfo testId="catalogs-info">
        Ninguna publicación coincide con la búsqueda.
      </RecommendationInfo>
    );
  }
  return <PublicationList items={papers} />;
}

type CatalogListProps = {
  items: CatalogRecommendationItemSchema[];
  matches: CatalogRecommendationItemSchema[];
  radiusArcsec?: number;
};

function CatalogList({
  items,
  matches,
  radiusArcsec,
}: Readonly<CatalogListProps>) {
  if (items.length === 0) {
    return (
      <RecommendationInfo testId="catalogs-empty">
        No se encontraron catálogos para esta región del cielo.
      </RecommendationInfo>
    );
  }
  if (matches.length === 0) {
    return (
      <RecommendationInfo testId="catalogs-info">
        Ningún catálogo coincide con la búsqueda.
      </RecommendationInfo>
    );
  }
  return (
    <div data-testid="catalog-list" className="flex flex-col gap-2 px-2 py-2">
      {matches.map((item) => (
        <CatalogueCard
          key={item.catalogue_id}
          item={item}
          radiusArcsec={radiusArcsec}
        />
      ))}
    </div>
  );
}

type PublicationListProps = {
  items: CatalogPublication[];
};

function PublicationList({ items }: Readonly<PublicationListProps>) {
  return (
    <div
      data-testid="publication-list"
      className="flex flex-col gap-2 px-2 py-2"
    >
      {items.map((publication) => (
        <PublicationCard key={publication.id} publication={publication} />
      ))}
    </div>
  );
}
