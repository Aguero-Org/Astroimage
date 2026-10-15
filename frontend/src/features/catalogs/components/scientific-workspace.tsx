import { PanelRightClose, PanelRightOpen, X } from "lucide-react";
import {
  type CSSProperties,
  type ReactNode,
  type PointerEvent as ReactPointerEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import type { RecommendCatalogsParams } from "@/api/generated/model";
import { Button } from "@/components/ui/button";
import { HelpHint } from "@/components/ui/help-hint";
import { Input } from "@/components/ui/input";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarProvider,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  type CatalogueMatchFilter,
  filterCatalogues,
  filterPublications,
  type PublicationKindFilter,
  regionDescription,
} from "../catalog-recommendations";
import { useCatalogRecommendations } from "../use-catalog-recommendations";
import { CatalogueCard } from "./catalogue-card";
import { PublicationCard } from "./publication-card";
import {
  RecommendationError,
  RecommendationInfo,
  RecommendationLoading,
} from "./recommendation-states";

type ScientificWorkspaceProps = {
  recordId: string;
  enabled: boolean;
  params: RecommendCatalogsParams | undefined;
  image: ReactNode;
  preview?: string;
};

const DEFAULT_WIDTH_PX = 360;
const MIN_WIDTH_PX = 300;
const MIN_VIEWPORT_MARGIN_PX = 160;

export function ScientificWorkspace({
  recordId,
  enabled,
  params,
  preview,
  image,
}: Readonly<ScientificWorkspaceProps>) {
  const [open, setOpen] = useState(false);
  const [width, setWidth] = useState(DEFAULT_WIDTH_PX);
  const openedFor = useRef<string | null>(null);

  const startResize = useCallback(
    (event: ReactPointerEvent<HTMLButtonElement>) => {
      event.preventDefault();
      const startX = event.clientX;
      const startWidth = width;
      const maxWidth =
        window.innerWidth -
        Math.min(MIN_VIEWPORT_MARGIN_PX, window.innerWidth - MIN_WIDTH_PX);
      const clamp = (value: number) =>
        Math.min(
          Math.max(value, MIN_WIDTH_PX),
          Math.max(MIN_WIDTH_PX, maxWidth),
        );

      function onMove(move: PointerEvent) {
        setWidth(clamp(startWidth + (startX - move.clientX)));
      }
      function onUp() {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        document.body.style.userSelect = "";
      }
      document.body.style.userSelect = "none";
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [width],
  );

  useEffect(() => {
    if (openedFor.current !== recordId) {
      openedFor.current = null;
      setOpen(false);
    }
  }, [recordId]);

  useEffect(() => {
    if (enabled && openedFor.current !== recordId) {
      openedFor.current = recordId;
      setOpen(true);
    }
  }, [enabled, recordId]);

  return (
    <SidebarProvider
      open={open}
      onOpenChange={setOpen}
      data-testid="scientific-workspace"
      className="h-full w-full"
      style={{ "--sidebar-width": `${width}px` } as CSSProperties}
    >
      <div className="relative min-w-0 flex-1">
        {image}
        <ScientificToggle />
      </div>
      <ScientificSidebar
        recordId={recordId}
        enabled={enabled}
        params={params}
        preview={preview}
        onResizeStart={startResize}
      />
    </SidebarProvider>
  );
}

function ScientificToggle() {
  const { open, openMobile, isMobile, toggleSidebar } = useSidebar();
  const expanded = isMobile ? openMobile : open;

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      data-testid="scientific-toggle"
      aria-expanded={expanded}
      aria-label={
        expanded
          ? "Cerrar exploración científica"
          : "Abrir exploración científica"
      }
      onClick={toggleSidebar}
      className="fixed top-1/2 z-40 h-10 -translate-y-1/2 rounded-r-none rounded-l-md border border-sidebar-border bg-sidebar text-sidebar-foreground shadow-sm"
      style={{ right: expanded ? "var(--sidebar-width)" : 0 }}
    >
      {expanded ? (
        <PanelRightClose className="size-4" />
      ) : (
        <PanelRightOpen className="size-4" />
      )}
    </Button>
  );
}

type ScientificSidebarProps = {
  recordId: string;
  enabled: boolean;
  params: RecommendCatalogsParams | undefined;
  preview: string | undefined;
  onResizeStart: (event: ReactPointerEvent<HTMLButtonElement>) => void;
};

function ScientificSidebar({
  recordId,
  enabled,
  params,
  preview,
  onResizeStart,
}: Readonly<ScientificSidebarProps>) {
  const { setOpen } = useSidebar();
  const {
    result,
    publications,
    isLoading,
    isFetching,
    isError,
    errorMessage,
    refetch,
  } = useCatalogRecommendations({ recordId, enabled, params });
  const [tab, setTab] = useState<"catalogs" | "papers">("catalogs");
  const [query, setQuery] = useState("");
  const [match, setMatch] = useState<CatalogueMatchFilter>("all");
  const [kind, setKind] = useState<PublicationKindFilter>("all");

  const items = result?.recommendations ?? [];
  const catalogues = filterCatalogues(items, { query, match });
  const papers = filterPublications(publications, query, kind);
  const activeCount = tab === "catalogs" ? items.length : publications.length;
  const showControls = activeCount >= 2;
  const updating = isFetching && result !== undefined;
  const region = regionDescription(result);

  const body = renderContent();

  return (
    <Sidebar
      side="right"
      variant="floating"
      collapsible="offcanvas"
      className="top-14"
    >
      <button
        type="button"
        aria-label="Redimensionar exploración científica"
        data-testid="scientific-resize"
        onPointerDown={onResizeStart}
        className="absolute inset-y-2 -left-1 z-30 hidden w-2 cursor-col-resize touch-none rounded-full bg-transparent transition-colors hover:bg-sidebar-border md:block"
      />
      <div
        data-testid="scientific-sidebar"
        className="flex h-full min-h-0 w-full flex-1 flex-col"
      >
        <SidebarHeader className="gap-2 border-b border-sidebar-border">
          <div className="flex items-start justify-between gap-2">
            <div className="flex min-w-0 flex-1 items-start gap-2">
              {preview ? (
                <img
                  src={preview}
                  alt="Vista previa de la región consultada"
                  data-testid="scientific-preview"
                  className="size-14 shrink-0 rounded-md border border-sidebar-border bg-black object-cover"
                />
              ) : null}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1">
                  <span className="text-sm font-semibold">
                    Exploración científica
                  </span>
                  <HelpHint
                    label="Exploración científica"
                    testId="help-scientific"
                    glossaryId="exploracion-cientifica"
                  >
                    Catálogos de VizieR y publicaciones sugeridos para la región
                    del cielo que cubre esta imagen.
                  </HelpHint>
                </div>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Catálogos y publicaciones que cubren esta imagen.
                </p>
                {region ? (
                  <span className="mt-0.5 flex items-center gap-1">
                    <span
                      data-testid="scientific-region"
                      className="truncate text-[11px] text-muted-foreground"
                    >
                      {region}
                    </span>
                    <HelpHint
                      label="Región consultada"
                      testId="help-region"
                      glossaryId="region-consultada"
                    >
                      Centro y radio del cielo usados para buscar catálogos, a
                      partir de la posición (WCS) de la imagen.
                    </HelpHint>
                  </span>
                ) : null}
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-7"
              data-testid="scientific-close"
              aria-label="Cerrar exploración científica"
              onClick={() => setOpen(false)}
            >
              <X className="size-4" />
            </Button>
          </div>
          {updating ? (
            <p className="text-[11px] text-muted-foreground">Actualizando…</p>
          ) : null}
        </SidebarHeader>

        <div
          role="tablist"
          aria-label="Recomendaciones"
          className="flex gap-1 px-2 pt-2"
        >
          <TabButton
            id="catalogs"
            label={`Catálogos (${items.length})`}
            active={tab === "catalogs"}
            onSelect={() => setTab("catalogs")}
          />
          <TabButton
            id="papers"
            label={`Publicaciones (${publications.length})`}
            active={tab === "papers"}
            onSelect={() => setTab("papers")}
          />
        </div>

        <p
          data-testid="scientific-explainer"
          className="px-2 pt-2 text-[11px] text-muted-foreground"
        >
          {tab === "catalogs"
            ? "Un catálogo es una tabla de fuentes del cielo (estrellas, galaxias, etc.) con sus posiciones y propiedades. Se listan los que cubren esta imagen."
            : "Una publicación es un trabajo científico sobre los datos. Se listan los artículos de cada catálogo y las referencias de su documentación."}
        </p>

        {showControls ? (
          <div className="flex flex-col gap-2 px-2 pt-2">
            <Input
              data-testid="catalog-search"
              type="search"
              value={query}
              aria-label={
                tab === "catalogs" ? "Buscar catálogos" : "Buscar publicaciones"
              }
              placeholder={
                tab === "catalogs"
                  ? "Buscar por nombre, autores o identificador"
                  : "Buscar por bibcode, DOI o catálogo"
              }
              onChange={(event) => setQuery(event.target.value)}
            />
            {tab === "catalogs" ? (
              <div className="flex items-center gap-1">
                <FilterChips
                  legend="Tipo de coincidencia"
                  name="catalogue-match"
                  testIdPrefix="catalog-filter"
                  options={MATCH_OPTIONS}
                  value={match}
                  onSelect={setMatch}
                />
                <HelpHint
                  label="Coincidencia por objeto"
                  testId="help-match"
                  glossaryId="coincidencia-objeto"
                >
                  Objeto identificado significa que el identificador aparece en
                  el catálogo. Solo catálogo indica cobertura de la región sin
                  esa coincidencia.
                </HelpHint>
              </div>
            ) : (
              <FilterChips
                legend="Tipo de publicación"
                name="publication-kind"
                testIdPrefix="publication-filter"
                options={KIND_OPTIONS}
                value={kind}
                onSelect={setKind}
              />
            )}
          </div>
        ) : null}

        <SidebarContent className="pb-24">{body}</SidebarContent>
      </div>
    </Sidebar>
  );

  function renderContent() {
    if (!enabled) {
      return (
        <RecommendationInfo testId="catalogs-info">
          Las recomendaciones aparecerán cuando termine el análisis de Gaia.
        </RecommendationInfo>
      );
    }
    if (isError) {
      return <RecommendationError message={errorMessage} onRetry={refetch} />;
    }
    if (isLoading) {
      return <RecommendationLoading />;
    }
    if (!result) {
      return (
        <RecommendationInfo testId="catalogs-info">
          Todavía no hay recomendaciones para esta imagen.
        </RecommendationInfo>
      );
    }
    if (result.error) {
      return <RecommendationError message={result.error} onRetry={refetch} />;
    }
    if (result.wcs_present === false) {
      return (
        <RecommendationInfo testId="catalogs-info">
          Esta imagen no tiene información de posición (WCS), así que no se
          puede ubicar su región en el cielo para buscar catálogos.
        </RecommendationInfo>
      );
    }
    if (result.queried === false) {
      return (
        <RecommendationInfo testId="catalogs-info">
          No se pudo consultar VizieR para esta región del cielo.
        </RecommendationInfo>
      );
    }
    if (tab === "catalogs") {
      if (items.length === 0) {
        return (
          <RecommendationInfo testId="catalogs-empty">
            No se encontraron catálogos para esta región del cielo.
          </RecommendationInfo>
        );
      }
      if (catalogues.length === 0) {
        return (
          <RecommendationInfo testId="catalogs-info">
            Ningún catálogo coincide con la búsqueda.
          </RecommendationInfo>
        );
      }
      return (
        <div
          data-testid="catalog-list"
          className="flex flex-col gap-2 px-2 py-2"
        >
          {catalogues.map((item) => (
            <CatalogueCard
              key={item.catalogue_id}
              item={item}
              radiusArcsec={result.radius_arcsec}
            />
          ))}
        </div>
      );
    }
    if (publications.length === 0) {
      return (
        <RecommendationInfo testId="papers-empty">
          {result.include_papers === false
            ? "Las publicaciones no se incluyeron en esta consulta."
            : "No se encontraron publicaciones asociadas a estos catálogos."}
        </RecommendationInfo>
      );
    }
    if (papers.length === 0) {
      return (
        <RecommendationInfo testId="catalogs-info">
          Ninguna publicación coincide con la búsqueda.
        </RecommendationInfo>
      );
    }
    return (
      <div
        data-testid="publication-list"
        className="flex flex-col gap-2 px-2 py-2"
      >
        {papers.map((publication) => (
          <PublicationCard key={publication.id} publication={publication} />
        ))}
      </div>
    );
  }
}

const MATCH_OPTIONS: { value: CatalogueMatchFilter; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "object", label: "Con objeto" },
  { value: "catalogue", label: "Solo catálogo" },
];

const KIND_OPTIONS: { value: PublicationKindFilter; label: string }[] = [
  { value: "all", label: "Todas" },
  { value: "catalogue-paper", label: "Artículo del catálogo" },
  { value: "readme-reference", label: "Referencia del ReadMe" },
];

type FilterChipsProps<T extends string> = {
  legend: string;
  name: string;
  testIdPrefix: string;
  options: { value: T; label: string }[];
  value: T;
  onSelect: (value: T) => void;
};

function FilterChips<T extends string>({
  legend,
  name,
  testIdPrefix,
  options,
  value,
  onSelect,
}: Readonly<FilterChipsProps<T>>) {
  return (
    <fieldset
      data-testid={`${testIdPrefix}-group`}
      className="flex flex-wrap items-center gap-3 text-xs"
    >
      <legend className="sr-only">{legend}</legend>
      {options.map((option) => (
        <label key={option.value} className="inline-flex items-center gap-1">
          <input
            type="radio"
            name={name}
            value={option.value}
            checked={value === option.value}
            data-testid={`${testIdPrefix}-${option.value}`}
            onChange={() => onSelect(option.value)}
          />
          {option.label}
        </label>
      ))}
    </fieldset>
  );
}

type TabButtonProps = {
  id: string;
  label: string;
  active: boolean;
  onSelect: () => void;
};

function TabButton({ id, label, active, onSelect }: Readonly<TabButtonProps>) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      data-testid={`scientific-tab-${id}`}
      className={
        active
          ? "rounded-md bg-sidebar-accent px-2 py-1 text-xs font-medium text-sidebar-accent-foreground"
          : "rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-sidebar-accent/50"
      }
      onClick={onSelect}
    >
      {label}
    </button>
  );
}
