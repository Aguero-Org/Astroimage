import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { glossaryPath } from "@/features/glossary/entries";
import { MOCK_EXTENDED_SOURCE, MOCK_POINT_SOURCE } from "@/mocks/data/image";
import { SourceSelection } from "./source-selection";

describe("SourceSelection", () => {
  it("shows point-source fields when a marker is selected", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <SourceSelection source={MOCK_POINT_SOURCE} />
      </TooltipProvider>,
    );

    expect(screen.getByTestId("meta-sel-snr")).toHaveTextContent("11.20");
    expect(screen.getByTestId("meta-sel-peak")).toBeInTheDocument();
    expect(screen.getByTestId("meta-sel-flux")).toBeInTheDocument();
  });

  it("shows extended-source fields when an extended marker is selected", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <SourceSelection source={MOCK_EXTENDED_SOURCE} />
      </TooltipProvider>,
    );

    expect(screen.getByTestId("extended-source-selection")).toBeInTheDocument();
    expect(screen.getByTestId("meta-sel-score")).toHaveTextContent("0.720");
    expect(screen.getByTestId("meta-sel-width")).toHaveTextContent("24.0 px");
    expect(screen.getByTestId("meta-sel-area")).toHaveTextContent("640 px²");
    expect(screen.getByTestId("meta-sel-mean")).toHaveTextContent("3.200");
  });

  it("shows the Gaia counterpart of the selected source", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <SourceSelection
          source={MOCK_POINT_SOURCE}
          gaiaMatch={{
            source_id: MOCK_POINT_SOURCE.source_id,
            object_type: "point",
            rank: 1,
            gaia_match: true,
            gaia_source_id: "123",
            gaia_separation_arcsec: 0.42,
            gaia_probability: 0.93,
          }}
        />
      </TooltipProvider>,
    );

    expect(screen.getByTestId("meta-sel-gaia-match")).toHaveTextContent(
      "Con contraparte",
    );
    expect(screen.getByTestId("meta-sel-gaia-separation")).toHaveTextContent(
      "0.42″",
    );
    expect(screen.getByText("Separación")).toBeInTheDocument();
    expect(screen.getByTestId("meta-sel-gaia-probability")).toHaveTextContent(
      "93%",
    );
    expect(screen.getByText("Probabilidad")).toBeInTheDocument();
    expect(screen.getByTestId("meta-sel-gaia-id")).toHaveTextContent("123");
    expect(screen.getByText("Gaia")).toBeInTheDocument();
    expect(screen.getByText("Gaia source")).toBeInTheDocument();
  });

  it.each([
    [
      "help-sel-gaia-match",
      /coincide con una fuente del catálogo Gaia/,
      "gaia",
    ],
    [
      "help-sel-gaia-separation",
      /Distancia angular entre la detección/,
      "radio-cruce",
    ],
    [
      "help-sel-gaia-probability",
      /Baja con la separación/,
      "exponente-probabilidad",
    ],
    ["help-sel-gaia-id", /Identificador de la fuente Gaia/, "gaia"],
  ])("explains %s and links its glossary entry", async (testId, text, id) => {
    const user = userEvent.setup();
    render(
      <TooltipProvider delayDuration={0}>
        <SourceSelection
          source={MOCK_POINT_SOURCE}
          gaiaMatch={{
            source_id: MOCK_POINT_SOURCE.source_id,
            object_type: "point",
            rank: 1,
            gaia_match: true,
            gaia_source_id: "123",
            gaia_separation_arcsec: 0.42,
            gaia_probability: 0.93,
          }}
        />
      </TooltipProvider>,
    );

    await user.hover(screen.getByTestId(testId));
    expect(await screen.findByText(text)).toBeInTheDocument();
    expect(screen.getByTestId(`${testId}-glossary`)).toHaveAttribute(
      "href",
      glossaryPath(id),
    );
  });

  it("shows the nearest separation when Gaia has no counterpart", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <SourceSelection
          source={MOCK_POINT_SOURCE}
          gaiaMatch={{
            source_id: MOCK_POINT_SOURCE.source_id,
            object_type: "point",
            rank: 1,
            gaia_match: false,
            gaia_separation_arcsec: 12.4,
            gaia_probability: 0,
          }}
        />
      </TooltipProvider>,
    );

    expect(screen.getByTestId("meta-sel-gaia-match")).toHaveTextContent(
      "Sin contraparte",
    );
    expect(screen.getByTestId("meta-sel-gaia-separation")).toHaveTextContent(
      "12.40″",
    );
    expect(screen.getByTestId("meta-sel-gaia-probability")).toHaveTextContent(
      "0%",
    );
    expect(screen.queryByTestId("meta-sel-gaia-id")).not.toBeInTheDocument();
  });

  it("omits the separation when the catalogue had no objects", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <SourceSelection
          source={MOCK_POINT_SOURCE}
          gaiaMatch={{
            source_id: MOCK_POINT_SOURCE.source_id,
            object_type: "point",
            rank: 1,
            gaia_match: false,
            gaia_probability: 0,
          }}
        />
      </TooltipProvider>,
    );

    expect(
      screen.queryByTestId("meta-sel-gaia-separation"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("meta-sel-gaia-probability")).toHaveTextContent(
      "0%",
    );
  });

  it("omits the separation when the nearest source is outside the radius", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <SourceSelection
          source={MOCK_POINT_SOURCE}
          gaiaMatch={{
            source_id: MOCK_POINT_SOURCE.source_id,
            object_type: "point",
            rank: 1,
            gaia_match: false,
            gaia_separation_arcsec: null,
            gaia_probability: 0,
          }}
        />
      </TooltipProvider>,
    );

    expect(
      screen.queryByTestId("meta-sel-gaia-separation"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("meta-sel-gaia-probability")).toHaveTextContent(
      "0%",
    );
  });
});
