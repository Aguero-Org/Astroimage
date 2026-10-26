import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
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
          <Button
            type="button"
            variant="ghost"
            aria-label="Ir a la página anterior"
            className="gap-1 pl-2.5"
            disabled={page <= 1}
            onClick={() => onPage(page - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Anterior</span>
          </Button>
        </PaginationItem>
        <PaginationItem>
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-current="page"
            disabled
          >
            {page}
          </Button>
        </PaginationItem>
        <PaginationItem>
          <Button
            type="button"
            variant="ghost"
            aria-label="Ir a la página siguiente"
            className="gap-1 pr-2.5"
            disabled={!hasMore}
            onClick={() => onPage(page + 1)}
          >
            <span>Siguiente</span>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
}
