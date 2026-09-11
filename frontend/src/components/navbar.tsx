import { useNavigate, useSearch } from "@tanstack/react-router";
import { BrandLogo } from "@/components/brand-logo";
import { ThemeToggle } from "@/components/theme-toggle";
import { ImageSearch } from "@/features/images/components/image-search";

export function Navbar() {
  const navigate = useNavigate();
  const search = useSearch({ strict: false });
  const urlQuery = typeof search.query === "string" ? search.query : "";

  return (
    <header
      data-testid="navbar"
      className="border-b border-sidebar-border bg-sidebar text-sidebar-foreground"
    >
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-3 px-4 py-3 sm:gap-6 sm:px-6 md:max-w-6xl md:px-8 lg:px-12 xl:max-w-7xl xl:px-16">
        <button
          type="button"
          data-testid="navbar-logo"
          className="flex shrink-0 cursor-pointer items-center gap-2"
          onClick={() => navigate({ to: "/", search: { query: "" } })}
        >
          <BrandLogo className="h-8 w-8" />
          <span className="text-lg font-semibold">Astroimage</span>
        </button>
        <div className="flex min-w-0 items-center gap-2">
          <ImageSearch
            variant="navbar"
            value={urlQuery}
            onSearch={(query) => navigate({ to: "/", search: { query } })}
          />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
