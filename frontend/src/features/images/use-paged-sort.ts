import { useState } from "react";

export function usePagedSort<Field extends string>(
  initialSort: Field,
  initialOrder: "asc" | "desc",
) {
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState(initialSort);
  const [order, setOrder] = useState<"asc" | "desc">(initialOrder);

  function toggleSort(field: Field) {
    if (field === sort) {
      setOrder((current) => (current === "asc" ? "desc" : "asc"));
    } else {
      setSort(field);
      setOrder("asc");
    }
    setPage(1);
  }

  return { page, setPage, sort, order, toggleSort };
}
