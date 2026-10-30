import { useNavigate, useSearch } from "@tanstack/react-router";
import type { RecordSortField } from "./api";
import type { CandidateSortField } from "./candidate-api";

type PagedSortKeys = {
  page: "page" | "cpage";
  sort: "sort" | "csort";
  order: "order" | "corder";
};

type SortFieldName = RecordSortField | CandidateSortField;

export function usePagedSort<Field extends SortFieldName>(
  keys: PagedSortKeys,
  initialSort: Field,
  initialOrder: "asc" | "desc",
) {
  const search = useSearch({ from: "/" });
  const navigate = useNavigate({ from: "/" });

  const page = search[keys.page];
  const sort = (search[keys.sort] ?? initialSort) as Field;
  const order = search[keys.order] ?? initialOrder;

  function setPage(nextPage: number) {
    const clamped = Math.max(1, Math.trunc(nextPage));
    void navigate({
      search: (prev) => ({ ...prev, [keys.page]: clamped }),
    });
  }

  function toggleSort(field: Field) {
    void navigate({
      search: (prev) => {
        const next = { ...prev };
        if (field === sort) {
          next[keys.order] = order === "asc" ? "desc" : "asc";
        } else {
          if (keys.sort === "sort") {
            next.sort = field as RecordSortField;
          } else {
            next.csort = field as CandidateSortField;
          }
          next[keys.order] = "asc";
        }
        next[keys.page] = 1;
        return next;
      },
    });
  }

  return { page, setPage, sort, order, toggleSort };
}
