import { createFileRoute } from "@tanstack/react-router";
import { ImageList } from "@/features/images/components/image-list";
import { ImageSearch } from "@/features/images/components/image-search";

export const Route = createFileRoute("/")({
  validateSearch: (search: Record<string, unknown>) => ({
    query: (search.query as string) ?? "",
  }),
  component: HomePage,
});

function HomePage() {
  const { query } = Route.useSearch();
  const navigate = Route.useNavigate();

  return (
    <main className="flex min-h-svh flex-col items-center gap-6 p-6">
      <div className="flex flex-col items-center gap-2 pt-10">
        <img src="/favicon.svg" alt="astroimage" className="h-32 w-32" />
        <h1 className="text-2xl font-semibold">Astroimage</h1>
      </div>
      <ImageSearch
        value={query}
        onSearch={(q) => navigate({ to: "/", search: { query: q } })}
      />
      <ImageList query={query} />
    </main>
  );
}
