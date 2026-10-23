import { describe, expect, it, vi } from "vitest";
import { pendingJobId, polledJobResult } from "./polled-job";

type Status = { job_id: string };
type Result = { value: string };

const isJob = (value: Status | Result | undefined): value is Status =>
  value !== undefined && "job_id" in value;
const isResult = (value: Status | Result | undefined): value is Result =>
  value !== undefined && "value" in value;

function query<T>(
  data: T | undefined,
  overrides: Record<string, unknown> = {},
) {
  return {
    data,
    isFetching: false,
    isError: false,
    refetch: vi.fn(),
    ...overrides,
  };
}

function combine(
  startData: Status | Result | undefined,
  jobData: Status | Result | undefined,
) {
  return polledJobResult({
    start: query(startData),
    job: query(jobData),
    isJob,
    isResult,
  });
}

describe("pendingJobId", () => {
  it("returns the id only while the answer is a job", () => {
    expect(pendingJobId({ job_id: "job-1" }, isJob)).toBe("job-1");
    expect(pendingJobId({ value: "done" }, isJob)).toBeUndefined();
    expect(pendingJobId(undefined, isJob)).toBeUndefined();
  });
});

describe("polledJobResult", () => {
  it("prefers the job result once it settles", () => {
    const view = combine({ job_id: "job-1" }, { value: "from-job" });

    expect(view.result).toEqual({ value: "from-job" });
  });

  it("falls back to a result returned by the start query", () => {
    expect(combine({ value: "from-start" }, undefined).result).toEqual({
      value: "from-start",
    });
  });

  it("has no result while the job is still pending", () => {
    expect(combine({ job_id: "job-1" }, { job_id: "job-1" }).result).toBe(
      undefined,
    );
  });

  it("is fetching when either query is fetching", () => {
    const idle = combine(undefined, undefined);
    expect(idle.isFetching).toBe(false);

    const startBusy = polledJobResult({
      start: query({ job_id: "job-1" }, { isFetching: true }),
      job: query(undefined),
      isJob,
      isResult,
    });
    expect(startBusy.isFetching).toBe(true);

    const jobBusy = polledJobResult({
      start: query({ job_id: "job-1" }),
      job: query(undefined, { isFetching: true }),
      isJob,
      isResult,
    });
    expect(jobBusy.isFetching).toBe(true);
  });

  it("merges loading, error, and error details from both queries", () => {
    const startError = new Error("start failed");
    const view = polledJobResult({
      start: query(
        { job_id: "job-1" },
        { isFetching: true, error: startError },
      ),
      job: query(undefined, { isFetching: true, isError: true }),
      isJob,
      isResult,
    });

    expect(view.isFetching).toBe(true);
    expect(view.isError).toBe(true);
    expect(view.error).toBe(startError);
  });

  it("refetches the pending job too", () => {
    const start = query<Status | Result>({ job_id: "job-1" });
    const job = query<Status | Result>(undefined);
    const view = polledJobResult({ start, job, isJob, isResult });

    view.refetch();

    expect(start.refetch).toHaveBeenCalledTimes(1);
    expect(job.refetch).toHaveBeenCalledTimes(1);
  });

  it("only refetches the start query when there is no job", () => {
    const start = query<Status | Result>({ value: "done" });
    const job = query<Status | Result>(undefined);
    const view = polledJobResult({ start, job, isJob, isResult });

    view.refetch();

    expect(start.refetch).toHaveBeenCalledTimes(1);
    expect(job.refetch).not.toHaveBeenCalled();
  });
});
