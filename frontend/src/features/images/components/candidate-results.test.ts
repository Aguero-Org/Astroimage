import { describe, expect, it } from "vitest";
import type { CandidatePageSchema } from "@/api/generated/model";
import { resultsView } from "./candidate-results";

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

type SearchState = Parameters<typeof resultsView>[0];

const IDLE: SearchState = {
  data: undefined,
  isPlaceholderData: false,
  isPending: false,
  isFetching: false,
  isError: false,
};

describe("resultsView", () => {
  it("reports an error before looking at the data", () => {
    expect(resultsView({ ...IDLE, isError: true, data: READY_PAGE })).toEqual({
      status: "error",
    });
  });

  it("reports loading while the first page is pending", () => {
    expect(resultsView({ ...IDLE, isPending: true })).toEqual({
      status: "loading",
    });
  });

  it("reports loading while a stale page is being replaced", () => {
    const view = resultsView({
      ...IDLE,
      data: READY_PAGE,
      isPlaceholderData: true,
      isFetching: true,
    });
    expect(view).toEqual({ status: "loading" });
  });

  it("reports idle when nothing was requested and nothing is in flight", () => {
    expect(resultsView(IDLE)).toEqual({ status: "idle" });
  });

  it("reports empty for a page without items", () => {
    expect(resultsView({ ...IDLE, data: EMPTY_PAGE })).toEqual({
      status: "empty",
      page: EMPTY_PAGE,
    });
  });

  it("reports ready for a page with items", () => {
    expect(resultsView({ ...IDLE, data: READY_PAGE })).toEqual({
      status: "ready",
      page: READY_PAGE,
    });
  });
});
