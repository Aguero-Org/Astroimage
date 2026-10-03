import { QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryHistory,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LAST_IMAGE_RECORD_KEY } from "@/features/images/last-record";
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
  afterEach(() => {
    sessionStorage.removeItem(LAST_IMAGE_RECORD_KEY);
  });

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

  it("highlights the hashed entry and copies its link", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    renderGlossary("fwhm");

    await waitFor(() => {
      expect(screen.getByTestId("glossary-entry-fwhm")).toBeInTheDocument();
    });
    expect(screen.getByTestId("glossary-entry-fwhm")).toHaveAttribute(
      "data-active",
      "true",
    );
    expect(screen.getByTestId("glossary-toc")).toBeInTheDocument();
    await user.click(screen.getByTestId("glossary-copy-fwhm"));
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining("/glossary#fwhm"),
    );
  });

  it("links back to the last opened viewer", async () => {
    sessionStorage.setItem(LAST_IMAGE_RECORD_KEY, "m31");
    renderGlossary();

    await waitFor(() => {
      expect(screen.getByTestId("glossary-back-to-viewer")).toHaveAttribute(
        "href",
        "/image/m31",
      );
    });
  });
});
