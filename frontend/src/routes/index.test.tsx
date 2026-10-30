import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { renderWithRouter } from "@/test/router";

describe("HomePage search", () => {
  it("filters the mock list from the home search", async () => {
    const user = userEvent.setup();
    renderWithRouter();

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

    await waitFor(
      () => {
        expect(screen.getByTestId("image-list")).toHaveTextContent(
          "M42 - Orion Nebula",
        );
      },
      { timeout: 8000 },
    );
    expect(screen.getByTestId("image-list")).not.toHaveTextContent(
      "M31 - Andromeda Galaxy",
    );
  });

  it("renders the stored list from pagination and sort URL params", async () => {
    renderWithRouter("/?page=2&sort=display_name&order=asc");

    await waitFor(
      () => {
        expect(screen.getByTestId("image-list")).toHaveTextContent(
          "M31 - Andromeda Galaxy",
        );
      },
      { timeout: 8000 },
    );
  });
});
