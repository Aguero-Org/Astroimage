import { describe, expect, it } from "vitest";
import type { CandidatePageSchema } from "@/api/generated/model";
import { type ResultsSearch, resultsView } from "../results-view";

const EMPTY_PAGE: CandidatePageSchema = {
  items: [],
  page: 1,
  limit: 8,
  has_more: false,
  sort: "product_filename",
  order: "asc",
};

const READY_PAGE: CandidatePageSchema = {
  ...EMPTY_PAGE,
  items: [
    {
      data_uri: "mast:HST/product.fits",
      product_filename: "product.fits",
      token: "token",
      instrument: "WFPC2",
      proposal_id: "1234",
      observation_id: "obs-1",
      filters: "F606W",
      observed_at: "2020-01-01",
      size_bytes: 1024,
      ra_deg: 10,
      dec_deg: 20,
    },
  ],
};

type SearchState = ResultsSearch<CandidatePageSchema>;

const IDLE: SearchState = {
  data: undefined,
  isPlaceholderData: false,
  isPending: false,
  isFetching: false,
  isError: false,
};

function view(search: SearchState, keepPlaceholder = false) {
  return resultsView(search, {
    keepPlaceholder,
    isEmpty: (page) => page.items.length === 0,
  });
}

describe("resultsView", () => {
  it("reports an error before looking at the data", () => {
    expect(view({ ...IDLE, isError: true, data: READY_PAGE })).toEqual({
      status: "error",
    });
  });

  it("reports loading while the first page is pending", () => {
    expect(view({ ...IDLE, isPending: true })).toEqual({
      status: "loading",
    });
  });

  it("reports loading while a stale page is being replaced", () => {
    expect(
      view({
        ...IDLE,
        data: READY_PAGE,
        isPlaceholderData: true,
        isFetching: true,
      }),
    ).toEqual({ status: "loading" });
  });

  it("keeps the stale page when the caller asks for it", () => {
    expect(
      view(
        {
          ...IDLE,
          data: READY_PAGE,
          isPlaceholderData: true,
          isFetching: true,
        },
        true,
      ),
    ).toEqual({ status: "ready", page: READY_PAGE });
  });

  it("reports idle when nothing was requested and nothing is in flight", () => {
    expect(view(IDLE)).toEqual({ status: "idle" });
  });

  it("reports empty for a page without items", () => {
    expect(view({ ...IDLE, data: EMPTY_PAGE })).toEqual({
      status: "empty",
      page: EMPTY_PAGE,
    });
  });

  it("reports ready for a page with items", () => {
    expect(view({ ...IDLE, data: READY_PAGE })).toEqual({
      status: "ready",
      page: READY_PAGE,
    });
  });

  it("uses the caller's emptiness check", () => {
    const recordsPage = { records: [], has_more: false };

    expect(
      resultsView(
        { ...IDLE, data: recordsPage },
        { isEmpty: (page) => page.records.length === 0 },
      ),
    ).toEqual({ status: "empty", page: recordsPage });
  });
});
