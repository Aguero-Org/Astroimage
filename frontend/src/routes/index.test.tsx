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
        expect(screen.getByTestId("home-title")).toBeInTheDocument();
        expect(screen.getByTestId("image-list")).toHaveTextContent(
          "M31 - Andromeda Galaxy",
        );
      },
      { timeout: 8000 },
    );

    const search = screen.getByTestId("search-input");
    await user.clear(search);
    await user.type(search, "orion");
    await user.click(screen.getByTestId("search-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("image-list")).toHaveTextContent(
        "M42 - Orion Nebula",
      );
    });
    expect(screen.getByTestId("image-list")).not.toHaveTextContent(
      "M31 - Andromeda Galaxy",
    );
  });
});
