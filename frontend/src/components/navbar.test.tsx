import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { Navbar } from "./navbar";

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
  Link: ({ to, children, ...props }: { to: string; children: ReactNode }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

describe("Navbar", () => {
  it("renders a search button with a magnifying-glass icon", () => {
    render(<Navbar />);

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("navbar-logo")).toBeInTheDocument();
    expect(screen.getByTestId("navbar-glossary")).toHaveTextContent("Glosario");
    expect(
      screen.getByTestId("navbar-glossary").querySelector("svg"),
    ).not.toBeNull();
    const searchButton = screen.getByTestId("search-submit");
    expect(searchButton.querySelector("svg")).not.toBeNull();
    expect(searchButton.className).toContain("cursor-pointer");
  });
});
