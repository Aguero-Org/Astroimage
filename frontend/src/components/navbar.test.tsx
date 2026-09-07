import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Navbar } from "./navbar";

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}));

describe("Navbar", () => {
  it("renders a search button with a magnifying-glass icon", () => {
    render(<Navbar />);

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("navbar-logo")).toBeInTheDocument();
    const searchButton = screen.getByTestId("search-submit");
    expect(searchButton.querySelector("svg")).not.toBeNull();
    expect(searchButton.className).toContain("cursor-pointer");
  });
});
