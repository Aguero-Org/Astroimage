import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { GaiaMatchSchema } from "@/api/generated/model";
import { TooltipProvider } from "@/components/ui/tooltip";
import {
  GaiaCrossMatch,
  gaiaMatchedIds,
  gaiaMatchFor,
  useGaiaCrossMatch,
} from "./gaia-cross-match";

const verify = vi.fn();
const job = vi.fn();

vi.mock("@/api/generated/sources/sources", () => ({
  useVerifySourcesGaia: (...args: unknown[]) => verify(...args),
  useGetSourcesGaiaJob: (...args: unknown[]) => job(...args),
}));

const idle = {
  data: undefined,
  isFetching: false,
  isError: false,
  refetch: vi.fn(),
};

function GaiaHarness({ enabled }: { enabled: boolean }) {
  const gaia = useGaiaCrossMatch("m31", {}, enabled);
  return (
    <TooltipProvider delayDuration={0}>
      <GaiaCrossMatch
        isFetching={gaia.isFetching}
        isError={gaia.isError}
        summary={gaia.summary}
        queried={gaia.queried}
        error={gaia.error}
        completed={gaia.completed}
        onRetry={gaia.refetch}
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
  beforeEach(() => {
    verify.mockReset();
    job.mockReset();
  });

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

    expect(screen.getByTestId("gaia-status")).toHaveTextContent(
      "Cruce con Gaia",
    );
    expect(screen.getByTestId("gaia-summary")).toHaveTextContent(
      "Puntuales 2/4",
    );
    expect(screen.getByTestId("gaia-matches")).toHaveTextContent("1");
    expect(screen.queryByTestId("gaia-unqueried")).not.toBeInTheDocument();
    expect(screen.queryByTestId("gaia-loading")).not.toBeInTheDocument();
  });

  it("keeps the summary visible while refreshing", () => {
    verify.mockReturnValue({
      ...verifyResponse(),
      isFetching: true,
    });
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled />);

    expect(screen.getByTestId("gaia-summary")).toHaveTextContent(
      "Puntuales 2/4",
    );
    expect(screen.queryByTestId("gaia-loading")).not.toBeInTheDocument();
    expect(screen.queryByTestId("gaia-unqueried")).not.toBeInTheDocument();
  });

  it("polls a pending Gaia job until it completes", () => {
    verify.mockReturnValue({
      ...idle,
      data: { status: "pending", job_id: "job-1", record_id: "m31" },
    });
    job.mockReturnValue(verifyResponse());
    render(<GaiaHarness enabled />);

    expect(screen.getByTestId("gaia-summary")).toHaveTextContent(
      "Puntuales 2/4",
    );
    expect(job).toHaveBeenLastCalledWith(
      "m31",
      "job-1",
      expect.objectContaining({
        query: expect.objectContaining({ enabled: true }),
      }),
    );
  });

  it("stays idle until detection finishes", () => {
    verify.mockReturnValue(idle);
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled={false} />);

    expect(verify).toHaveBeenLastCalledWith(
      "m31",
      {},
      expect.objectContaining({
        query: expect.objectContaining({ enabled: false }),
      }),
    );
    expect(screen.queryByTestId("gaia-summary")).not.toBeInTheDocument();
    expect(screen.getByTestId("gaia-matches")).toBeEmptyDOMElement();
    expect(job).toHaveBeenLastCalledWith(
      "m31",
      "",
      expect.objectContaining({
        query: expect.objectContaining({ enabled: false }),
      }),
    );
  });

  it("shows the query error and lets the user retry", async () => {
    const user = userEvent.setup();
    const retry = vi.fn();
    verify.mockReturnValue({
      ...verifyResponse(),
      refetch: retry,
      data: {
        ...verifyResponse().data,
        queried: false,
        error: "Gaia query failed: 429",
      },
    });
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled />);

    expect(screen.getByTestId("gaia-error")).toHaveTextContent(
      "Gaia no respondió",
    );
    expect(screen.queryByTestId("gaia-summary")).not.toBeInTheDocument();
    expect(screen.queryByTestId("gaia-unqueried")).not.toBeInTheDocument();
    expect(screen.queryByTestId("gaia-loading")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(retry).toHaveBeenCalledTimes(1);
  });

  it("shows the loading state while the crossmatch runs", () => {
    verify.mockReturnValue({
      ...idle,
      isFetching: true,
    });
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled />);

    expect(screen.getByTestId("gaia-status")).toHaveTextContent(
      "Cruzando con Gaia…",
    );
    expect(screen.getByTestId("gaia-loading")).toBeInTheDocument();
  });

  it("handles a summary with only point sources", () => {
    verify.mockReturnValue({
      ...verifyResponse(),
      data: {
        ...verifyResponse().data,
        summary: { point: { count: 4, matched: 2 } },
      },
    });
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled />);

    expect(screen.getByTestId("gaia-summary")).toHaveTextContent(
      "Extendidas 0/0",
    );
  });

  it("handles a summary with only extended sources", () => {
    verify.mockReturnValue({
      ...verifyResponse(),
      data: {
        ...verifyResponse().data,
        summary: { extended: { count: 1, matched: 1 } },
      },
    });
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled />);

    expect(screen.getByTestId("gaia-summary")).toHaveTextContent(
      "Puntuales 0/0",
    );
  });

  it("polls only while the Gaia job is pending", () => {
    verify.mockReturnValue({
      ...idle,
      data: { status: "pending", job_id: "job-1", record_id: "m31" },
    });
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled />);

    const options = job.mock.calls.at(-1)?.[2] as
      | { query?: { refetchInterval?: (query: unknown) => unknown } }
      | undefined;
    expect(
      options?.query?.refetchInterval?.({
        state: { data: { status: "pending" } },
      }),
    ).toBe(2000);
    expect(
      options?.query?.refetchInterval?.({
        state: { data: { status: "completed" } },
      }),
    ).toBe(false);
  });

  it("treats a completed answer without queried as not queried", () => {
    verify.mockReturnValue({
      ...verifyResponse(),
      data: {
        ...verifyResponse().data,
        queried: undefined,
      },
    });
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled />);

    expect(screen.getByTestId("gaia-unqueried")).toBeInTheDocument();
    expect(screen.queryByTestId("gaia-summary")).not.toBeInTheDocument();
  });

  it("reports when the image has no sky coordinates", () => {
    verify.mockReturnValue({
      ...idle,
      data: {
        ...verifyResponse().data,
        queried: false,
        error: null,
      },
    });
    job.mockReturnValue(idle);
    render(<GaiaHarness enabled />);

    expect(screen.getByTestId("gaia-unqueried")).toHaveTextContent(
      "no tiene coordenadas celestes",
    );
    expect(screen.queryByTestId("gaia-error")).not.toBeInTheDocument();
    expect(screen.queryByTestId("gaia-summary")).not.toBeInTheDocument();
  });
});

describe("Gaia match helpers", () => {
  const matches: GaiaMatchSchema[] = [
    { source_id: 1, object_type: "point", rank: 1, gaia_match: true },
    { source_id: 2, object_type: "point", rank: 2, gaia_match: false },
    { source_id: 3, object_type: "extended", rank: 1, gaia_match: true },
    { source_id: 4, object_type: "extended", rank: 2, gaia_match: false },
  ];

  it("collects matched source ids by object type", () => {
    expect([...gaiaMatchedIds(matches, "point")]).toEqual([1]);
    expect([...gaiaMatchedIds(matches, "extended")]).toEqual([3]);
  });

  it("finds a match by source id and object type", () => {
    expect(gaiaMatchFor(matches, 2, "point")?.source_id).toBe(2);
    expect(gaiaMatchFor(matches, 2, "extended")).toBeUndefined();
  });
});

function verifyResponse() {
  return {
    data: {
      status: "completed",
      match_radius_arcsec: 1,
      probability_power: 1,
      queried: true,
      error: null,
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
    isFetching: false,
    isError: false,
    refetch: vi.fn(),
  };
}
