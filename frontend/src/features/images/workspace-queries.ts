type RenderQueryGate = {
  isSuccess: boolean;
  isFetching: boolean;
};

export function followOnQueriesEnabled(renderQuery: RenderQueryGate): boolean {
  return renderQuery.isSuccess && !renderQuery.isFetching;
}
