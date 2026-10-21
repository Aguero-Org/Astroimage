import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type {
  CatalogRecommendationItemSchema,
  CatalogRecommendationResponse,
} from "@/api/generated/model";
import { TooltipProvider } from "@/components/ui/tooltip";
import type { CatalogPublication } from "../catalog-recommendations";
import { RecommendationContent } from "./scientific-recommendation-content";

const ITEM: CatalogRecommendationItemSchema = {
  rank: 1,
  catalogue_id: "gaia",
  match_type: "CATALOGUE_ONLY",
};

const PUBLICATION: CatalogPublication = {
  id: "paper-1",
  bibcode: "2026A&A...1A",
  kind: "catalogue-paper",
  catalogueIds: ["gaia"],
  catalogueNames: ["Gaia"],
};

const RESULT: CatalogRecommendationResponse = {
  status: "completed",
  radius_arcsec: 60,
  recommendations: [ITEM],
};

type ContentProps = Parameters<typeof RecommendationContent>[0];

function content(overrides: Partial<ContentProps> = {}) {
  return (
    <TooltipProvider>
      <RecommendationContent
        enabled
        isError={false}
        isLoading={false}
        result={RESULT}
        tab="catalogs"
        items={[ITEM]}
        matches={[ITEM]}
        publications={[]}
        papers={[]}
        errorMessage="boom"
        onRetry={vi.fn()}
        {...overrides}
      />
    </TooltipProvider>
  );
}

function renderContent(overrides: Partial<ContentProps> = {}) {
  return render(content(overrides));
}

describe("RecommendationContent", () => {
  it("waits for Gaia before showing results", () => {
    renderContent({ enabled: false });

    expect(screen.getByTestId("catalogs-info")).toHaveTextContent(/Gaia/);
  });

  it("shows the request error and retries", () => {
    renderContent({ isError: true });

    expect(screen.getByTestId("recommendations-error")).toHaveTextContent(
      /boom/,
    );
  });

  it("shows the loading state", () => {
    renderContent({ isLoading: true });

    expect(screen.getByTestId("recommendations-loading")).toBeInTheDocument();
  });

  it("shows the empty state before a result arrives", () => {
    renderContent({ result: undefined });

    expect(screen.getByTestId("catalogs-info")).toHaveTextContent(
      /Todavía no hay recomendaciones/,
    );
  });

  it("turns a result error into the retry state", () => {
    renderContent({ result: { ...RESULT, error: "vizier down" } });

    expect(screen.getByTestId("recommendations-error")).toHaveTextContent(
      /vizier down/,
    );
  });

  it("explains when the image has no WCS", () => {
    renderContent({ result: { ...RESULT, wcs_present: false } });

    expect(screen.getByTestId("catalogs-info")).toHaveTextContent(/WCS/);
  });

  it("explains when VizieR was not queried", () => {
    renderContent({ result: { ...RESULT, queried: false } });

    expect(screen.getByTestId("catalogs-info")).toHaveTextContent(/VizieR/);
  });

  it("shows the catalogue empty states", () => {
    const { rerender } = renderContent({ items: [], matches: [] });

    expect(screen.getByTestId("catalogs-empty")).toBeInTheDocument();

    rerender(content({ items: [ITEM], matches: [] }));
    expect(screen.getByTestId("catalogs-info")).toHaveTextContent(
      /Ningún catálogo coincide/,
    );
  });

  it("distinguishes papers excluded from the request from no papers found", () => {
    const { rerender } = renderContent({
      tab: "papers",
      result: { ...RESULT, include_papers: false },
    });

    expect(screen.getByTestId("papers-empty")).toHaveTextContent(
      /no se incluyeron/,
    );

    rerender(content({ tab: "papers" }));
    expect(screen.getByTestId("papers-empty")).toHaveTextContent(
      /No se encontraron publicaciones/,
    );
  });

  it("shows filtered and unfiltered publication lists", () => {
    const { rerender } = renderContent({
      tab: "papers",
      publications: [PUBLICATION],
      papers: [],
    });

    expect(screen.getByTestId("catalogs-info")).toHaveTextContent(
      /Ninguna publicación coincide/,
    );

    rerender(
      content({
        tab: "papers",
        publications: [PUBLICATION],
        papers: [PUBLICATION],
      }),
    );
    expect(screen.getByTestId("publication-list")).toBeInTheDocument();
  });
});
