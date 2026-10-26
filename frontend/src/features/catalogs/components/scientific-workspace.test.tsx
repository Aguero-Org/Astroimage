import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { MOCK_SIMBAD_OBJECT } from "@/mocks/data/simbad";
import { createTestQueryClient } from "@/test/render";
import { server } from "@/test/server";
import type { SimbadReferencesView } from "../use-simbad-references";
import { ScientificWorkspace } from "./scientific-workspace";

const CATALOGS_URL = "http://localhost:8000/image/m31/catalogs/recommendations";

function simbadView(
  overrides: Partial<SimbadReferencesView> = {},
): SimbadReferencesView {
  return {
    objects: [],
    result: undefined,
    isError: false,
    isLoading: false,
    isFetching: false,
    errorMessage: "error desconocido",
    refetch: vi.fn(),
    summary: undefined,
    ...overrides,
  };
}

function renderWorkspace(
  enabled: boolean,
  preview?: string,
  simbad: SimbadReferencesView = simbadView(),
  selectedSource: {
    source_id: number;
    object_type: "point" | "extended";
  } | null = null,
) {
  const queryClient = createTestQueryClient();
  const workspace = (nextEnabled: boolean, nextSource = selectedSource) => (
    <QueryClientProvider client={queryClient}>
      <ScientificWorkspace
        recordId="m31"
        enabled={nextEnabled}
        params={undefined}
        preview={preview}
        simbad={simbad}
        selectedSource={nextSource ? { ...nextSource } : null}
        image={<div data-testid="image-canvas" />}
      />
    </QueryClientProvider>
  );
  const result = render(workspace(enabled));
  return {
    result,
    rerenderEnabled: (nextEnabled: boolean) =>
      result.rerender(workspace(nextEnabled)),
    rerenderWorkspace: (
      nextEnabled: boolean,
      nextSource: typeof selectedSource,
    ) => result.rerender(workspace(nextEnabled, nextSource)),
  };
}

describe("ScientificWorkspace", () => {
  it("waits for Gaia before requesting recommendations", () => {
    renderWorkspace(false);

    expect(screen.getByTestId("catalogs-info")).toHaveTextContent(/Gaia/);
    expect(screen.queryByTestId("catalog-list")).not.toBeInTheDocument();
    expect(screen.getByTestId("image-canvas")).toBeInTheDocument();
    expect(screen.getByTestId("scientific-toggle")).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("opens when Gaia finishes after the workspace mounted", async () => {
    const { rerenderEnabled } = renderWorkspace(false);

    rerenderEnabled(true);

    await screen.findByTestId("catalog-list");
    expect(screen.getByTestId("scientific-toggle")).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });

  it("opens once enabled and closes from the close button", async () => {
    const user = userEvent.setup();
    renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    expect(screen.getByTestId("scientific-toggle")).toHaveAttribute(
      "aria-expanded",
      "true",
    );

    await user.click(screen.getByTestId("scientific-close"));
    expect(screen.getByTestId("scientific-toggle")).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("does not reopen after the user closes it for that record", async () => {
    const user = userEvent.setup();
    const { rerenderEnabled } = renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    await user.click(screen.getByTestId("scientific-close"));
    rerenderEnabled(false);
    rerenderEnabled(true);

    expect(screen.getByTestId("scientific-toggle")).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("opens SIMBAD when a source is selected", async () => {
    renderWorkspace(true, undefined, simbadView(), {
      source_id: 1,
      object_type: "point",
    });

    expect(await screen.findByTestId("simbad-empty")).toBeInTheDocument();
    expect(screen.getByTestId("scientific-tab-simbad")).toHaveAttribute(
      "data-state",
      "active",
    );
  });

  it("opens SIMBAD when a source becomes selected", async () => {
    const user = userEvent.setup();
    const { rerenderWorkspace } = renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    await user.click(screen.getByTestId("scientific-tab-papers"));
    rerenderWorkspace(true, { source_id: 2, object_type: "point" });

    expect(await screen.findByTestId("simbad-empty")).toBeInTheDocument();
    expect(screen.getByTestId("scientific-tab-simbad")).toHaveAttribute(
      "data-state",
      "active",
    );
  });

  it("keeps the chosen tab when the workspace rerenders with the same source", async () => {
    const user = userEvent.setup();
    const { rerenderEnabled } = renderWorkspace(true, undefined, simbadView(), {
      source_id: 1,
      object_type: "point",
    });

    await screen.findByTestId("simbad-empty");
    await user.click(screen.getByTestId("scientific-tab-papers"));
    expect(screen.getByTestId("scientific-tab-papers")).toHaveAttribute(
      "data-state",
      "active",
    );

    rerenderEnabled(true);

    expect(screen.getByTestId("scientific-tab-papers")).toHaveAttribute(
      "data-state",
      "active",
    );
  });

  it("loads catalogues and publications once enabled", async () => {
    renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    expect(screen.getByTestId("scientific-tab-catalogs")).toHaveTextContent(
      "Catálogos (4)",
    );
    expect(screen.getByTestId("scientific-tab-papers")).toHaveTextContent(
      "Publicaciones (3)",
    );
    expect(screen.getAllByTestId("catalogue-card")).toHaveLength(4);
  });

  it("shows the catalogue title, authors and description", async () => {
    renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    expect(
      screen.getAllByTestId("catalogue-card-name").at(0),
    ).toHaveTextContent("Gaia EDR3");
    expect(
      screen.getAllByTestId("catalogue-card-authors").at(0),
    ).toHaveTextContent("Gaia Collaboration");
    expect(
      screen.getAllByTestId("catalogue-card-description").at(0),
    ).toHaveTextContent(/Astrometría/);
    expect(screen.getByTestId("catalogue-card-keywords")).toHaveTextContent(
      /Astrometry/,
    );
    expect(screen.getByTestId("catalogue-card-object")).toHaveTextContent(
      /Este objeto está en el catálogo/,
    );
    expect(
      screen.queryByText(/Catálogo de la región/i),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/cubre esta región/i)).not.toBeInTheDocument();
  });

  it("shows the consulted region and preview when provided", async () => {
    renderWorkspace(true, "blob:preview");

    await screen.findByTestId("catalog-list");
    expect(screen.getByTestId("scientific-region")).toHaveTextContent(
      /RA 10\.6847° · Dec 41\.2691° · radio 60\.0″/,
    );
    expect(screen.getByTestId("scientific-preview")).toHaveAttribute(
      "src",
      "blob:preview",
    );
  });

  it("expands a catalogue card with details and links", async () => {
    const user = userEvent.setup();
    renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    const firstToggle = screen.getAllByTestId("catalogue-card-toggle").at(0);
    expect(firstToggle).toHaveAttribute("data-state", "closed");
    await user.click(firstToggle as HTMLElement);
    expect(firstToggle).toHaveAttribute("data-state", "open");
    const firstDetail = screen.getAllByTestId("catalogue-card-detail").at(0);
    expect(firstDetail).toBeInTheDocument();
    expect(
      within(firstDetail as HTMLElement).getByTestId("catalogue-link-vizier"),
    ).toHaveAttribute("href", expect.stringContaining("vizier"));
  });

  it("lists publications on the second tab", async () => {
    const user = userEvent.setup();
    renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    await user.click(screen.getByTestId("scientific-tab-papers"));
    expect(screen.getByTestId("publication-list")).toBeInTheDocument();
    expect(screen.getAllByTestId("publication-card")).toHaveLength(3);
    const firstLink = screen.getAllByTestId("publication-link").at(0);
    expect(firstLink).toHaveAttribute("target", "_blank");
    expect(screen.getAllByTestId("publication-label").at(0)).toHaveTextContent(
      "Gaia Early Data Release 3",
    );
    expect(screen.getByTestId("publication-abstract")).toHaveTextContent(
      /Astrometría y fotometría/,
    );
    expect(screen.queryByText(/Abrir el paper/i)).not.toBeInTheDocument();
  });

  it("explains catalogues and publications for the active tab", async () => {
    const user = userEvent.setup();
    renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    expect(screen.getByTestId("scientific-explainer")).toHaveTextContent(
      /Un catálogo es una tabla/i,
    );

    await user.click(screen.getByTestId("scientific-tab-papers"));
    expect(screen.getByTestId("scientific-explainer")).toHaveTextContent(
      /Una publicación es un trabajo científico/i,
    );
  });

  it("filters publications by kind", async () => {
    const user = userEvent.setup();
    renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    await user.click(screen.getByTestId("scientific-tab-papers"));
    expect(screen.getAllByTestId("publication-card")).toHaveLength(3);

    await user.click(screen.getByTestId("publication-filter-catalogue-paper"));
    expect(screen.getAllByTestId("publication-card")).toHaveLength(1);

    await user.click(screen.getByTestId("publication-filter-readme-reference"));
    expect(screen.getAllByTestId("publication-card")).toHaveLength(2);
  });

  it("exposes a resize handle", async () => {
    renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    expect(screen.getByTestId("scientific-resize")).toBeInTheDocument();
  });

  it("filters catalogues by match type", async () => {
    const user = userEvent.setup();
    renderWorkspace(true);

    await screen.findByTestId("catalog-list");
    await user.click(screen.getByTestId("catalog-filter-object"));
    expect(screen.getAllByTestId("catalogue-card")).toHaveLength(1);
  });

  it("shows an error and retries without restarting Gaia", async () => {
    server.use(
      http.get(
        CATALOGS_URL,
        () => HttpResponse.json({ detail: "boom" }, { status: 500 }),
        { once: true },
      ),
    );
    const user = userEvent.setup();
    renderWorkspace(true);

    await screen.findByTestId("recommendations-error");
    await user.click(screen.getByTestId("recommendations-retry"));
    expect(await screen.findByTestId("catalog-list")).toBeInTheDocument();
  });

  it("renders the SIMBAD view provided by the route", async () => {
    const user = userEvent.setup();
    renderWorkspace(
      true,
      undefined,
      simbadView({ objects: [MOCK_SIMBAD_OBJECT] }),
    );

    await screen.findByTestId("catalog-list");
    await user.click(screen.getByTestId("scientific-tab-simbad"));

    expect(screen.getByTestId("scientific-tab-simbad")).toHaveTextContent(
      "SIMBAD (1)",
    );
    expect(screen.getByTestId("simbad-object-card")).toBeInTheDocument();
  });

  it("retries SIMBAD through the view provided by the route", async () => {
    const user = userEvent.setup();
    const refetch = vi.fn();
    renderWorkspace(true, undefined, simbadView({ isError: true, refetch }));

    await screen.findByTestId("catalog-list");
    await user.click(screen.getByTestId("scientific-tab-simbad"));
    await user.click(screen.getByTestId("recommendations-retry"));

    expect(refetch).toHaveBeenCalledTimes(1);
  });
});
