import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type ImageSearchProps = {
  value: string;
  onSearch: (query: string) => void;
  isFetching?: boolean;
  variant: "hero" | "navbar";
};

export function ImageSearch({
  value,
  onSearch,
  isFetching = false,
  variant,
}: ImageSearchProps) {
  const [local, setLocal] = useState(value);
  const isNavbar = variant === "navbar";

  useEffect(() => {
    setLocal(value);
  }, [value]);

  return (
    <form
      className={cn(
        "flex items-center gap-2",
        isNavbar ? "min-w-0" : "mx-auto w-full max-w-lg",
      )}
      onSubmit={(event) => {
        event.preventDefault();
        onSearch(local);
      }}
    >
      <Input
        type="search"
        placeholder={
          isNavbar
            ? "Buscar por cuerpo celeste…"
            : "Buscar por cuerpo celeste, ej. M31, Orión…"
        }
        value={local}
        onChange={(event) => setLocal(event.target.value)}
        className={isNavbar ? "w-36 sm:w-52 md:w-64 lg:w-72" : "flex-1"}
        aria-label="Buscar imágenes"
        disabled={isFetching}
      />
      <Button
        type="submit"
        size={isNavbar ? "sm" : "default"}
        disabled={isFetching}
      >
        <Search className="size-4" />
        {isFetching ? "Buscando…" : "Buscar"}
      </Button>
    </form>
  );
}
