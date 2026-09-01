import { useNavigate } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useImageFetch } from "@/features/images/use-image-fetch";

export function Navbar() {
  const navigate = useNavigate();
  const fetchMutation = useImageFetch();
  const [query, setQuery] = useState("");

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (query.trim().length > 0) {
      fetchMutation.mutate(query);
    }
    navigate({ to: "/", search: { query } });
  }

  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-3 px-4 py-3 sm:gap-6 sm:px-6 md:max-w-6xl md:px-8 lg:px-12 xl:max-w-7xl xl:px-16">
        <button
          type="button"
          className="flex shrink-0 cursor-pointer items-center gap-2"
          onClick={() => navigate({ to: "/", search: { query: "" } })}
        >
          <img src="/favicon.svg" alt="astroimage" className="h-8 w-8" />
          <span className="text-lg font-semibold">Astroimage</span>
        </button>
        <form
          className="flex min-w-0 items-center gap-2"
          onSubmit={handleSubmit}
        >
          <Input
            type="search"
            placeholder="Buscar por cuerpo celeste…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-36 sm:w-52 md:w-64 lg:w-72"
            aria-label="Buscar imágenes"
            disabled={fetchMutation.isPending}
          />
          <Button type="submit" size="sm" disabled={fetchMutation.isPending}>
            <Search className="size-4" />
            {fetchMutation.isPending ? "Buscando…" : "Buscar"}
          </Button>
        </form>
      </div>
    </header>
  );
}
