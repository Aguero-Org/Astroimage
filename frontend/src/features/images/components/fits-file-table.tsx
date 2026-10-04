import { ArrowDown, ArrowUp } from "lucide-react";
import type { ReactNode } from "react";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Table, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export type FitsFileColumn<Field extends string = string> = {
  field: Field;
  label: string;
  hint?: ReactNode;
};

type FitsFileTableProps<Field extends string> = {
  columns: readonly FitsFileColumn<Field>[];
  trailingHead?: ReactNode;
  sort: Field;
  order: "asc" | "desc";
  onSort: (field: Field) => void;
  children: ReactNode;
  testId?: string;
};

export function FitsFileTable<Field extends string>({
  columns,
  trailingHead,
  sort,
  order,
  onSort,
  children,
  testId,
}: Readonly<FitsFileTableProps<Field>>) {
  return (
    <Table data-testid={testId}>
      <TableHeader>
        <TableRow>
          {columns.map((column) => {
            const active = sort === column.field;
            return (
              <TableHead
                key={column.field}
                aria-sort={
                  active
                    ? order === "asc"
                      ? "ascending"
                      : "descending"
                    : "none"
                }
              >
                <span className="inline-flex items-center gap-1">
                  <button
                    type="button"
                    className="inline-flex items-center gap-1"
                    onClick={() => onSort(column.field)}
                  >
                    {column.label}
                    {active && order === "asc" && (
                      <ArrowUp className="size-3" />
                    )}
                    {active && order === "desc" && (
                      <ArrowDown className="size-3" />
                    )}
                  </button>
                  {column.hint}
                </span>
              </TableHead>
            );
          })}
          {trailingHead}
        </TableRow>
      </TableHeader>
      {children}
    </Table>
  );
}

type FilePagerProps = {
  page: number;
  hasMore: boolean;
  onPage: (page: number) => void;
};

export function FilePager({ page, hasMore, onPage }: Readonly<FilePagerProps>) {
  if (page <= 1 && !hasMore) {
    return null;
  }
  return (
    <Pagination>
      <PaginationContent>
        <PaginationItem>
          <PaginationPrevious
            href="#"
            aria-disabled={page <= 1}
            className={page <= 1 ? "pointer-events-none opacity-50" : undefined}
            onClick={(event) => {
              event.preventDefault();
              if (page > 1) {
                onPage(page - 1);
              }
            }}
          />
        </PaginationItem>
        <PaginationItem>
          <PaginationLink
            href="#"
            isActive
            onClick={(event) => event.preventDefault()}
          >
            {page}
          </PaginationLink>
        </PaginationItem>
        <PaginationItem>
          <PaginationNext
            href="#"
            aria-disabled={!hasMore}
            className={hasMore ? undefined : "pointer-events-none opacity-50"}
            onClick={(event) => {
              event.preventDefault();
              if (hasMore) {
                onPage(page + 1);
              }
            }}
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
}
