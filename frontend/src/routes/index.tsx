import { createFileRoute } from "@tanstack/react-router";
import { BrandLogo } from "@/components/brand-logo";
import { ThemeToggle } from "@/components/theme-toggle";
import { Separator } from "@/components/ui/separator";
import { GlossaryLink } from "@/features/glossary/glossary-link";
import { CandidateResults } from "@/features/images/components/candidate-results";
import { ImageList } from "@/features/images/components/image-list";
import { ImageSearch } from "@/features/images/components/image-search";

export const Route = createFileRoute("/")({
  validateSearch: (search: Record<string, unknown>) => ({
    query: typeof search.query === "string" ? search.query : "",
  }),
  component: HomePage,
});

function HomePage() {
  const { query } = Route.useSearch();
  const navigate = Route.useNavigate();

  return (
    <main className="relative flex min-h-svh flex-col items-center gap-6 p-6">
      <div className="absolute top-4 right-4 flex items-center gap-3">
        <GlossaryLink testId="home-glossary" />
        <ThemeToggle />
      </div>
      <div className="flex flex-col items-center gap-2 pt-10">
        <BrandLogo className="h-32 w-32" />
        <h1 data-testid="home-title" className="text-2xl font-semibold">
          Astroimage
        </h1>
      </div>
      <ImageSearch
        variant="hero"
        value={query}
        onSearch={(nextQuery) => {
          navigate({ to: "/", search: { query: nextQuery } });
        }}
      />
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <CandidateResults key={`candidates-${query}`} query={query} />
        {query.trim().length > 0 && <Separator />}
        <ImageList key={`stored-${query}`} query={query} />
      </div>
    </main>
  );
}
