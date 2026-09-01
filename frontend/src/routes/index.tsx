import { createFileRoute } from "@tanstack/react-router";
import { ImageList } from "@/features/images/components/image-list";
import { ImageSearch } from "@/features/images/components/image-search";
import { useImageFetch } from "@/features/images/use-image-fetch";

export const Route = createFileRoute("/")({
  validateSearch: (search: Record<string, unknown>) => ({
    query: (search.query as string) ?? "",
  }),
  component: HomePage,
});

function HomePage() {
  const { query } = Route.useSearch();
  const navigate = Route.useNavigate();
  const fetchMutation = useImageFetch();

  function handleSearch(q: string) {
    navigate({ to: "/", search: { query: q } });
    if (q.trim().length > 0) {
      fetchMutation.mutate(q);
    }
  }

  return (
    <main className="flex min-h-svh flex-col items-center gap-6 p-6">
      <div className="flex flex-col items-center gap-2 pt-10">
        <img src="/favicon.svg" alt="astroimage" className="h-32 w-32" />
        <h1 className="text-2xl font-semibold">Astroimage</h1>
      </div>
      <ImageSearch
        value={query}
        onSearch={handleSearch}
        isFetching={fetchMutation.isPending}
      />
      <ImageList
        query={query}
        isFetching={fetchMutation.isPending}
        fetchError={fetchMutation.error}
      />
    </main>
  );
}
