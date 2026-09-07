import { useNavigate, useSearch } from "@tanstack/react-router";
import { AppearanceControls } from "@/components/appearance-controls";
import { ImageSearch } from "@/features/images/components/image-search";

export function Navbar() {
  const navigate = useNavigate();
  const search = useSearch({ strict: false });
  const urlQuery = typeof search.query === "string" ? search.query : "";

  return (
    <header
      data-testid="navbar"
      className="border-b border-border bg-background/70 backdrop-blur-md"
    >
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-3 px-4 py-3 sm:gap-6 sm:px-6 md:max-w-6xl md:px-8 lg:px-12 xl:max-w-7xl xl:px-16">
        <button
          type="button"
          data-testid="navbar-logo"
          className="flex shrink-0 cursor-pointer items-center gap-2"
          onClick={() => navigate({ to: "/", search: { query: "" } })}
        >
          <img src="/favicon.svg" alt="astroimage" className="h-8 w-8" />
          <span className="text-lg font-semibold">Astroimage</span>
        </button>
        <div className="flex min-w-0 items-center gap-2">
          <ImageSearch
            variant="navbar"
            value={urlQuery}
            onSearch={(query) => navigate({ to: "/", search: { query } })}
          />
          <AppearanceControls />
        </div>
      </div>
    </header>
  );
}
