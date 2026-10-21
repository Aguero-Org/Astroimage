export type ResultsView<TPage> =
  | { status: "loading" }
  | { status: "error" }
  | { status: "idle" }
  | { status: "empty"; page: TPage }
  | { status: "ready"; page: TPage };

export type ResultsSearch<TPage> = {
  data: TPage | null | undefined;
  isPlaceholderData: boolean;
  isPending: boolean;
  isFetching: boolean;
  isError: boolean;
};

type ResultsViewOptions<TPage> = {
  keepPlaceholder?: boolean;
  isEmpty: (page: TPage) => boolean;
};

export function resultsView<TPage>(
  search: ResultsSearch<TPage>,
  { keepPlaceholder = false, isEmpty }: ResultsViewOptions<TPage>,
): ResultsView<TPage> {
  if (search.isError) {
    return { status: "error" };
  }
  const page =
    search.isPlaceholderData && !keepPlaceholder ? null : (search.data ?? null);
  if (page === null) {
    return search.isPending || search.isFetching
      ? { status: "loading" }
      : { status: "idle" };
  }
  return isEmpty(page) ? { status: "empty", page } : { status: "ready", page };
}
