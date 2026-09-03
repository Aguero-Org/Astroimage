import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ImageSearch } from "./image-search";

describe("ImageSearch", () => {
  it("submits the typed query from the hero layout", async () => {
    const onSearch = vi.fn();
    const user = userEvent.setup();
    render(<ImageSearch variant="hero" value="" onSearch={onSearch} />);

    await user.type(
      screen.getByRole("searchbox", { name: "Buscar imágenes" }),
      "orion",
    );
    await user.click(screen.getByRole("button", { name: "Buscar" }));

    expect(onSearch).toHaveBeenCalledWith("orion");
  });

  it("uses a compact control in the navbar layout", () => {
    render(<ImageSearch variant="navbar" value="" onSearch={vi.fn()} />);

    const field = screen.getByRole("searchbox", { name: "Buscar imágenes" });
    expect(field.className).toContain("w-36");
    expect(screen.getByRole("button", { name: "Buscar" }).className).toContain(
      "h-8",
    );
  });
});
