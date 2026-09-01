import { useNavigate } from "@tanstack/react-router";
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
      <div className="flex items-center gap-4 px-6 py-3">
        <button
          type="button"
          className="flex items-center gap-2"
          onClick={() => navigate({ to: "/", search: { query: "" } })}
        >
          <img src="/favicon.svg" alt="astroimage" className="h-8 w-8" />
          <span className="text-lg font-semibold">Astroimage</span>
        </button>
        <form
          className="ml-auto flex items-center gap-2"
          onSubmit={handleSubmit}
        >
          <Input
            type="search"
            placeholder="Search by celestial body…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-64"
            aria-label="Search images"
            disabled={fetchMutation.isPending}
          />
          <Button type="submit" size="sm" disabled={fetchMutation.isPending}>
            {fetchMutation.isPending ? "Searching…" : "Search"}
          </Button>
        </form>
      </div>
    </header>
  );
}
