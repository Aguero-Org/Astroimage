import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type ImageSearchProps = {
  value: string;
  onSearch: (query: string) => void;
  isFetching: boolean;
};

export function ImageSearch({ value, onSearch, isFetching }: ImageSearchProps) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  return (
    <form
      className="mx-auto flex w-full max-w-lg gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        onSearch(local);
      }}
    >
      <Input
        type="search"
        placeholder="Buscar por cuerpo celeste, ej. M31, Orión…"
        value={local}
        onChange={(e) => setLocal(e.target.value)}
        className="flex-1"
        aria-label="Buscar imágenes"
        disabled={isFetching}
      />
      <Button type="submit" disabled={isFetching}>
        <Search className="size-4" />
        {isFetching ? "Buscando…" : "Buscar"}
      </Button>
    </form>
  );
}
