import { Search } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type ImageSearchProps = {
  value: string;
  onSearch: (query: string) => void;
  isFetching?: boolean;
  variant: "hero" | "navbar";
};

export function ImageSearch(props: Readonly<ImageSearchProps>) {
  return <ImageSearchField key={props.value} {...props} />;
}

function ImageSearchField({
  value,
  onSearch,
  isFetching = false,
  variant,
}: Readonly<ImageSearchProps>) {
  const [local, setLocal] = useState(value);
  const isNavbar = variant === "navbar";

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
        data-testid="search-input"
        placeholder={
          isNavbar
            ? "Nombre, archivo o cuerpo celeste…"
            : "Nombre, archivo, instrumento, propuesta, fuente o cuerpo celeste…"
        }
        value={local}
        onChange={(event) => setLocal(event.target.value)}
        className={isNavbar ? "w-36 sm:w-52 md:w-64 lg:w-72" : "flex-1"}
        aria-label="Buscar imágenes"
        disabled={isFetching}
      />
      <Button
        type="submit"
        data-testid="search-submit"
        size={isNavbar ? "sm" : "default"}
        disabled={isFetching}
      >
        <Search className="size-4" />
        {isFetching ? "Buscando…" : "Buscar"}
      </Button>
      <HelpHint label="Objeto celeste" testId="help-objeto" glossaryId="objeto">
        Nombre del cielo, como M31 o NGC 1300. También acepta archivo o
        instrumento y lista los recortes.
      </HelpHint>
    </form>
  );
}
