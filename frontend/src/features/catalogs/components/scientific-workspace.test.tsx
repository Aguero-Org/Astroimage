import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { createTestQueryClient } from "@/test/render";
import { server } from "@/test/server";
import { ScientificWorkspace } from "./scientific-workspace";

const CATALOGS_URL = "http://localhost:8000/image/m31/catalogs/recommendations";

function renderWorkspace(enabled: boolean, preview?: string) {
  const queryClient = createTestQueryClient();
  const workspace = (nextEnabled: boolean) => (
    <QueryClientProvider client={queryClient}>
      <ScientificWorkspace
        recordId="m31"
        enabled={nextEnabled}
        params={undefined}
        preview={preview}
        image={<div data-testid="image-canvas" />}
      />
    </QueryClientProvider>
  );
  const result = render(workspace(enabled));
  return {
    result,
    rerenderEnabled: (nextEnabled: boolean) =>
      result.rerender(workspace(nextEnabled)),
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
});
