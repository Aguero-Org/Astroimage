import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { MOCK_SIMBAD_OBJECT } from "@/mocks/data/simbad";
import { SimbadObjectCard } from "./simbad-object-card";

describe("SimbadObjectCard", () => {
  it("shows only the summary when collapsed", () => {
    render(<SimbadObjectCard object={MOCK_SIMBAD_OBJECT} />);

    expect(screen.getByTestId("simbad-object-name")).toHaveTextContent(
      /M\s+31/,
    );
    expect(screen.getByTestId("simbad-object-otype")).toHaveTextContent(
      "Galaxia",
    );
    expect(screen.getByTestId("simbad-object-source")).toHaveTextContent(
      "Fuente puntual #1",
    );
    expect(screen.getByTestId("simbad-object-simbad-link")).toHaveAttribute(
      "href",
      "https://simbad.cds.unistra.fr/simbad/sim-id?Ident=M%20%2031",
    );
    expect(screen.queryByText("Tipo espectral")).not.toBeInTheDocument();
  });

  it("reveals details after expanding", async () => {
    const user = userEvent.setup();
    render(<SimbadObjectCard object={MOCK_SIMBAD_OBJECT} />);

    await user.click(screen.getByTestId("simbad-object-toggle"));

    expect(screen.getByText("Tipo espectral")).toBeInTheDocument();
    expect(screen.getByText("RA")).toBeInTheDocument();
    expect(screen.getByText("2450")).toBeInTheDocument();
    expect(screen.getByText("Andromeda Galaxy")).toBeInTheDocument();
  });
});
