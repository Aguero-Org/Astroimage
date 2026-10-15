import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { GaiaCrossMatch, useGaiaCrossMatch } from "./gaia-cross-match";

const verify = vi.fn();
const job = vi.fn();

vi.mock("@/api/generated/sources/sources", () => ({
  useVerifySourcesGaia: (...args: unknown[]) => verify(...args),
  useGetSourcesGaiaJob: (...args: unknown[]) => job(...args),
}));

const idle = { data: undefined, isFetching: false, isError: false };

function GaiaHarness({ enabled }: { enabled: boolean }) {
  const gaia = useGaiaCrossMatch("m31", {}, enabled);
  return (
    <TooltipProvider delayDuration={0}>
      <GaiaCrossMatch
        isFetching={gaia.isFetching}
        isError={gaia.isError}
        summary={gaia.summary}
      />
      <ul data-testid="gaia-matches">
        {gaia.matches.map((match) => (
          <li key={match.source_id}>{match.source_id}</li>
        ))}
      </ul>
    </TooltipProvider>
  );
}

describe("GaiaCrossMatch", () => {
  it("cross-matches when detection is ready and reports the summary", () => {
    verify.mockImplementation(
      (
        _recordId: string,
        _params: unknown,
        options?: { query?: { enabled?: boolean } },
      ) => (options?.query?.enabled ? verifyResponse() : idle),
    );
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled />);

    expect(screen.getByTestId("gaia-summary")).toHaveTextContent(
      "Puntuales 2/4",
    );
    expect(screen.getByTestId("gaia-matches")).toHaveTextContent("1");
  });

  it("stays idle until detection finishes", () => {
    verify.mockReturnValue(idle);
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled={false} />);

    expect(verify).toHaveBeenCalledWith(
      "m31",
      {},
      { query: { enabled: false } },
    );
    expect(screen.queryByTestId("gaia-summary")).not.toBeInTheDocument();
  });
});

function verifyResponse() {
  return {
    data: {
      status: 200,
      data: {
        match_radius_arcsec: 1,
        probability_power: 1,
        summary: {
          point: { count: 4, matched: 2 },
          extended: { count: 1, matched: 0 },
        },
        matches: [
          {
            source_id: 1,
            object_type: "point",
            rank: 1,
            gaia_match: true,
          },
        ],
      },
    },
    isFetching: false,
    isError: false,
  };
}
