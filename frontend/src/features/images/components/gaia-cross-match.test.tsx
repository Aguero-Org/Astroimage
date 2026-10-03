import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { GaiaCrossMatch } from "./gaia-cross-match";

const verify = vi.fn();
const job = vi.fn();

vi.mock("@/api/generated/sources/sources", () => ({
  useVerifySourcesGaia: (...args: unknown[]) => verify(...args),
  useGetSourcesGaiaJob: (...args: unknown[]) => job(...args),
}));

const idle = { data: undefined, isFetching: false, isError: false };

describe("GaiaCrossMatch", () => {
  it("requests a cross-match and reports the summary", async () => {
    const onMatches = vi.fn();
    verify.mockImplementation(
      (
        _recordId: string,
        _params: unknown,
        options?: { query?: { enabled?: boolean } },
      ) => {
        if (!options?.query?.enabled) {
          return idle;
        }
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
      },
    );
    job.mockReturnValue(idle);
    const user = userEvent.setup();
    render(
      <TooltipProvider delayDuration={0}>
        <GaiaCrossMatch recordId="m31" params={{}} onMatches={onMatches} />
      </TooltipProvider>,
    );

    await user.click(screen.getByTestId("gaia-cross-match-submit"));

    expect(screen.getByTestId("gaia-summary")).toHaveTextContent(
      "Puntuales 2/4",
    );
    expect(onMatches).toHaveBeenCalledWith([
      expect.objectContaining({ source_id: 1, gaia_match: true }),
    ]);
  });
});
