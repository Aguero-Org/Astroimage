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

function renderHome(initialEntry = "/") {
  const queryClient = createTestQueryClient();
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: [initialEntry] }),
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

describe("HomePage search", () => {
  it("filters the mock list from the home search", async () => {
    const user = userEvent.setup();
    renderHome();

    await waitFor(
      () => {
        expect(screen.getByText("M31 - Andromeda Galaxy")).toBeInTheDocument();
      },
      { timeout: 8000 },
    );

    const search = screen.getByRole("searchbox", { name: "Buscar imágenes" });
    await user.clear(search);
    await user.type(search, "orion");
    await user.click(screen.getByRole("button", { name: "Buscar" }));

    await waitFor(() => {
      expect(screen.getByText("M42 - Orion Nebula")).toBeInTheDocument();
    });
    expect(
      screen.queryByText("M31 - Andromeda Galaxy"),
    ).not.toBeInTheDocument();
  });
});
