type JobStatus = { job_id: string };

export type JobQueryView<TBody> = {
  data: TBody | undefined;
  isFetching: boolean;
  isError: boolean;
  error?: unknown;
  refetch: () => unknown;
};

export function pendingJobId<TStatus extends JobStatus, TResult>(
  body: TStatus | TResult | undefined,
  isJob: (value: TStatus | TResult | undefined) => value is TStatus,
): string | undefined {
  return isJob(body) ? body.job_id : undefined;
}

/**
 * Some endpoints answer with a job id first and the result once the job
 * settles. Each feature still owns its generated query hooks; this only
 * combines the "start" and "job" queries into a single view.
 */
export function polledJobResult<TStatus extends JobStatus, TResult>({
  start,
  job,
  isJob,
  isResult,
}: {
  start: JobQueryView<TStatus | TResult>;
  job: JobQueryView<TStatus | TResult>;
  isJob: (value: TStatus | TResult | undefined) => value is TStatus;
  isResult: (value: TStatus | TResult | undefined) => value is TResult;
}) {
  const jobId = pendingJobId(start.data, isJob);
  const result = isResult(job.data)
    ? job.data
    : isResult(start.data)
      ? start.data
      : undefined;
  return {
    result,
    isFetching: start.isFetching || job.isFetching,
    isError: start.isError || job.isError,
    error: start.error ?? job.error,
    refetch: () => {
      void start.refetch();
      if (jobId !== undefined) {
        void job.refetch();
      }
    },
  };
}
