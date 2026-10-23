type JobStatus = { job_id: string };
type PolledJobBody<TStatus, TResult> = TStatus | TResult | undefined;

export type JobQueryView<TBody> = {
  data: TBody | undefined;
  isFetching: boolean;
  isError: boolean;
  error?: unknown;
  refetch: () => unknown;
};

export function pendingJobId<TStatus extends JobStatus, TResult>(
  body: PolledJobBody<TStatus, TResult>,
  isJob: (value: PolledJobBody<TStatus, TResult>) => value is TStatus,
): string | undefined {
  return isJob(body) ? body.job_id : undefined;
}

export function polledJobResult<TStatus extends JobStatus, TResult>({
  start,
  job,
  isJob,
  isResult,
}: {
  start: JobQueryView<TStatus | TResult>;
  job: JobQueryView<TStatus | TResult>;
  isJob: (value: PolledJobBody<TStatus, TResult>) => value is TStatus;
  isResult: (value: PolledJobBody<TStatus, TResult>) => value is TResult;
}) {
  const jobId = pendingJobId(start.data, isJob);
  let result: TResult | undefined;
  if (isResult(job.data)) {
    result = job.data;
  } else if (isResult(start.data)) {
    result = start.data;
  }
  return {
    result,
    isFetching: start.isFetching || job.isFetching,
    isError: start.isError || job.isError,
    error: start.error ?? job.error,
    refetch: () => {
      start.refetch();
      if (jobId !== undefined) {
        job.refetch();
      }
    },
  };
}
