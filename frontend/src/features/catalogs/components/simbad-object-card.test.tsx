import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
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
    expect(screen.getByTestId("simbad-object-match")).toHaveTextContent(
      "Fuente puntual #1",
    );
    expect(screen.getByTestId("simbad-object-separation")).toHaveTextContent(
      "0.15″",
    );
    expect(screen.getByTestId("simbad-object-probability")).toHaveTextContent(
      "98%",
    );
  });

  it("reports the nearest separation when there is no match", async () => {
    const user = userEvent.setup();
    render(
      <SimbadObjectCard
        object={{
          ...MOCK_SIMBAD_OBJECT,
          image_match: {
            source_id: 7,
            object_type: "point",
            separation_arcsec: 6.25,
            probability: 0,
            matched: false,
          },
        }}
      />,
    );

    await user.click(screen.getByTestId("simbad-object-toggle"));

    expect(screen.getByTestId("simbad-object-match")).toHaveTextContent(
      "Sin fuente cercana",
    );
    expect(screen.getByTestId("simbad-object-separation")).toHaveTextContent(
      "6.25″",
    );
    expect(screen.getByTestId("simbad-object-probability")).toHaveTextContent(
      "0%",
    );
    expect(screen.queryByTestId("simbad-object-focus")).not.toBeInTheDocument();
  });

  it("focuses an extended counterpart", async () => {
    const user = userEvent.setup();
    const onFocusSource = vi.fn();
    render(
      <SimbadObjectCard
        object={{
          ...MOCK_SIMBAD_OBJECT,
          image_match: {
            source_id: 7,
            object_type: "extended",
            separation_arcsec: 1.25,
            probability: 0.75,
            matched: true,
          },
        }}
        onFocusSource={onFocusSource}
      />,
    );

    await user.click(screen.getByTestId("simbad-object-toggle"));
    expect(screen.getByTestId("simbad-object-match")).toHaveTextContent(
      "Fuente extendida #7",
    );

    await user.click(screen.getByTestId("simbad-object-focus"));
    expect(onFocusSource).toHaveBeenCalledWith(7, "extended");
  });

  it("focuses a point counterpart", async () => {
    const user = userEvent.setup();
    const onFocusSource = vi.fn();
    render(
      <SimbadObjectCard
        object={{
          ...MOCK_SIMBAD_OBJECT,
          image_match: {
            source_id: 7,
            object_type: "point",
            separation_arcsec: 1.25,
            probability: 0.75,
            matched: true,
          },
        }}
        onFocusSource={onFocusSource}
      />,
    );

    await user.click(screen.getByTestId("simbad-object-toggle"));
    expect(screen.getByTestId("simbad-object-match")).toHaveTextContent(
      "Fuente puntual #7",
    );

    await user.click(screen.getByTestId("simbad-object-focus"));
    expect(onFocusSource).toHaveBeenCalledWith(7, "point");
  });

  it("does not offer focus without a callback", async () => {
    const user = userEvent.setup();
    render(<SimbadObjectCard object={MOCK_SIMBAD_OBJECT} />);

    await user.click(screen.getByTestId("simbad-object-toggle"));

    expect(screen.queryByTestId("simbad-object-focus")).not.toBeInTheDocument();
  });

  it("does not offer focus for an unmatched object", async () => {
    const user = userEvent.setup();
    const onFocusSource = vi.fn();
    render(
      <SimbadObjectCard
        object={{
          ...MOCK_SIMBAD_OBJECT,
          image_match: {
            source_id: 7,
            object_type: "point",
            separation_arcsec: 6.25,
            probability: 0,
            matched: false,
          },
        }}
        onFocusSource={onFocusSource}
      />,
    );

    await user.click(screen.getByTestId("simbad-object-toggle"));

    expect(screen.queryByTestId("simbad-object-focus")).not.toBeInTheDocument();
  });

  it("omits the match row when the image has no crossmatch", async () => {
    const user = userEvent.setup();
    render(
      <SimbadObjectCard
        object={{ ...MOCK_SIMBAD_OBJECT, image_match: undefined }}
      />,
    );

    await user.click(screen.getByTestId("simbad-object-toggle"));

    expect(screen.queryByTestId("simbad-object-match")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("simbad-object-separation"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("simbad-object-probability"),
    ).not.toBeInTheDocument();
  });
});
