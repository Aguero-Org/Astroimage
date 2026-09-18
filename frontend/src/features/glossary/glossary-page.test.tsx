import { QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { routeTree } from "@/routeTree.gen";
import { createTestQueryClient } from "@/test/render";

function renderGlossary(hash = "") {
  const queryClient = createTestQueryClient();
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({
      initialEntries: [hash ? `/glossary#${hash}` : "/glossary"],
    }),
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

describe("GlossaryPage", () => {
  it("groups entries and filters by name", async () => {
    const user = userEvent.setup();
    renderGlossary();

    await waitFor(() => {
      expect(screen.getByTestId("glossary-page")).toBeInTheDocument();
    });
    expect(screen.getByTestId("glossary-group-vista")).toBeInTheDocument();
    expect(screen.getByTestId("glossary-entry-fwhm")).toBeInTheDocument();

    await user.type(screen.getByTestId("glossary-search"), "FWHM");
    expect(screen.getByTestId("glossary-entry-fwhm")).toBeInTheDocument();
    expect(
      screen.queryByTestId("glossary-entry-stretch"),
    ).not.toBeInTheDocument();
  });
});
