import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

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
