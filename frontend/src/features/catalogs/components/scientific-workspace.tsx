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
import { Label } from "@/components/ui/label";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarProvider,
  useSidebar,
} from "@/components/ui/sidebar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  type CatalogueMatchFilter,
  filterCatalogues,
  filterPublications,
  type PublicationKindFilter,
  regionDescription,
} from "../catalog-recommendations";
import { simbadObjectsForSource } from "../simbad-references";
import { useCatalogRecommendations } from "../use-catalog-recommendations";
import type { SimbadReferencesView } from "../use-simbad-references";
import {
  RecommendationError,
  RecommendationInfo,
  RecommendationLoading,
} from "./recommendation-states";
import { RecommendationContent } from "./scientific-recommendation-content";
import { SimbadObjectCard } from "./simbad-object-card";

type ScientificWorkspaceProps = {
  recordId: string;
  enabled: boolean;
  params: RecommendCatalogsParams | undefined;
  image: ReactNode;
  preview?: string;
  selectedSource?: {
    source_id: number;
    object_type: "point" | "extended";
  } | null;
  onFocusSource?: (sourceId: number, objectType: "point" | "extended") => void;
  simbad: SimbadReferencesView;
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
  selectedSource,
  onFocusSource,
  simbad,
}: Readonly<ScientificWorkspaceProps>) {
  const [openRequest, setOpenRequest] = useState<boolean | null>(null);
  const [width, setWidth] = useState(DEFAULT_WIDTH_PX);
  const open = openRequest ?? enabled;

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

  return (
    <SidebarProvider
      open={open}
      onOpenChange={setOpenRequest}
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
        selectedSource={selectedSource}
        onFocusSource={onFocusSource}
        onResizeStart={startResize}
        simbad={simbad}
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
  selectedSource?: {
    source_id: number;
    object_type: "point" | "extended";
  } | null;
  onFocusSource?: (sourceId: number, objectType: "point" | "extended") => void;
  onResizeStart: (event: ReactPointerEvent<HTMLButtonElement>) => void;
  simbad: SimbadReferencesView;
};

type WorkspaceTab = "catalogs" | "papers" | "simbad";

function visibleCount(
  tab: WorkspaceTab,
  catalogues: number,
  publications: number,
  simbadObjects: number,
): number {
  if (tab === "catalogs") {
    return catalogues;
  }
  if (tab === "papers") {
    return publications;
  }
  return simbadObjects;
}

function tabExplainer(tab: WorkspaceTab): string {
  if (tab === "catalogs") {
    return "Un catálogo es una tabla de fuentes del cielo (estrellas, galaxias, etc.) con sus posiciones y propiedades. Se listan los que cubren esta imagen.";
  }
  if (tab === "papers") {
    return "Una publicación es un trabajo científico sobre los datos. Se listan los artículos de cada catálogo y las referencias de su documentación.";
  }
  return "SIMBAD reúne objetos astronómicos identificados, sus alias, propiedades y bibliografía. Se muestran los objetos que coinciden con las fuentes detectadas en esta imagen.";
}

function ScientificSidebar({
  recordId,
  enabled,
  params,
  preview,
  selectedSource,
  onFocusSource,
  onResizeStart,
  simbad,
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
  const [tab, setTab] = useState<"catalogs" | "papers" | "simbad">("catalogs");
  const simbadListRef = useRef<HTMLDivElement>(null);
  const [showNoMatchToast, setShowNoMatchToast] = useState(false);
  const lastFocusedRef = useRef<string | null>(null);
  const selectedSourceId = selectedSource?.source_id;
  const selectedSourceType = selectedSource?.object_type;

  useEffect(() => {
    if (enabled && selectedSourceId !== undefined) {
      setTab("simbad");
    }
  }, [enabled, selectedSourceId]);

  useEffect(() => {
    if (
      !enabled ||
      selectedSourceId === undefined ||
      selectedSourceType === undefined ||
      tab !== "simbad"
    ) {
      return undefined;
    }
    const matches = simbadObjectsForSource(
      simbad.objects,
      selectedSourceId,
      selectedSourceType,
    );
    const key = `${selectedSourceType}:${selectedSourceId}`;
    if (matches.length === 0) {
      if (lastFocusedRef.current === key) {
        return undefined;
      }
      lastFocusedRef.current = key;
      setShowNoMatchToast(true);
      const timer = window.setTimeout(() => setShowNoMatchToast(false), 2000);
      return () => window.clearTimeout(timer);
    }
    lastFocusedRef.current = key;
    setShowNoMatchToast(false);
    const target = matches[0];
    if (!target) {
      return undefined;
    }
    const id = `simbad-card-${target.main_id}`;
    const timer = window.setTimeout(() => {
      const element = document.getElementById(id);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "center" });
      } else if (simbadListRef.current) {
        simbadListRef.current.scrollTo({ top: 0, behavior: "smooth" });
      }
    }, 50);
    return () => window.clearTimeout(timer);
  }, [enabled, selectedSourceId, selectedSourceType, tab, simbad.objects]);

  const [query, setQuery] = useState("");
  const [match, setMatch] = useState<CatalogueMatchFilter>("all");
  const [kind, setKind] = useState<PublicationKindFilter>("all");

  const items = result?.recommendations ?? [];
  const catalogues = filterCatalogues(items, { query, match });
  const papers = filterPublications(publications, query, kind);
  const activeCount = visibleCount(
    tab,
    items.length,
    publications.length,
    simbad.objects.length,
  );
  const showControls = tab !== "simbad" && activeCount >= 2;
  const updating = isFetching && result !== undefined;
  const region = regionDescription(result);

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

        <Tabs
          value={tab}
          onValueChange={(value) =>
            setTab(value as "catalogs" | "papers" | "simbad")
          }
          className="flex min-h-0 flex-1 flex-col gap-0"
        >
          <TabsList
            aria-label="Recomendaciones"
            className="flex h-auto w-full justify-start gap-1 rounded-none bg-transparent p-0 px-2 pt-2"
          >
            <TabsTrigger
              value="catalogs"
              data-testid="scientific-tab-catalogs"
              className={TAB_TRIGGER_CLASS}
            >
              Catálogos ({items.length})
            </TabsTrigger>
            <TabsTrigger
              value="papers"
              data-testid="scientific-tab-papers"
              className={TAB_TRIGGER_CLASS}
            >
              Publicaciones ({publications.length})
            </TabsTrigger>
            <TabsTrigger
              value="simbad"
              data-testid="scientific-tab-simbad"
              className={TAB_TRIGGER_CLASS}
            >
              SIMBAD ({simbad.objects.length})
            </TabsTrigger>
          </TabsList>

          <p
            data-testid="scientific-explainer"
            className="px-2 pt-2 text-[11px] text-muted-foreground"
          >
            {tabExplainer(tab)}
          </p>

          {showControls ? (
            <div className="flex flex-col gap-2 px-2 pt-2">
              <Input
                data-testid="catalog-search"
                type="search"
                value={query}
                aria-label={
                  tab === "catalogs"
                    ? "Buscar catálogos"
                    : "Buscar publicaciones"
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
                    Objeto identificado significa que el identificador aparece
                    en el catálogo. Solo catálogo indica cobertura de la región
                    sin esa coincidencia.
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

          <SidebarContent className="pb-24">
            <TabsContent value="catalogs">
              <RecommendationContent
                enabled={enabled}
                isError={isError}
                isLoading={isLoading}
                result={result}
                tab="catalogs"
                items={items}
                matches={catalogues}
                publications={publications}
                papers={papers}
                errorMessage={errorMessage}
                onRetry={refetch}
              />
            </TabsContent>
            <TabsContent value="papers">
              <RecommendationContent
                enabled={enabled}
                isError={isError}
                isLoading={isLoading}
                result={result}
                tab="papers"
                items={items}
                matches={catalogues}
                publications={publications}
                papers={papers}
                errorMessage={errorMessage}
                onRetry={refetch}
              />
            </TabsContent>
            <TabsContent value="simbad">{renderSimbad()}</TabsContent>
          </SidebarContent>
        </Tabs>
      </div>
    </Sidebar>
  );

  function renderSimbad() {
    if (simbad.isError) {
      return (
        <RecommendationError
          message={simbad.errorMessage}
          onRetry={simbad.refetch}
        />
      );
    }
    if (simbad.isLoading) {
      return <RecommendationLoading />;
    }
    if (simbad.result?.wcs_present === false) {
      return (
        <RecommendationInfo testId="simbad-info">
          Esta imagen no tiene información de posición (WCS), así que no se
          puede ubicar su región en el cielo para buscar objetos SIMBAD.
        </RecommendationInfo>
      );
    }
    if (simbad.result?.queried === false) {
      return (
        <RecommendationInfo testId="simbad-info">
          No se pudo consultar SIMBAD para esta región del cielo.
        </RecommendationInfo>
      );
    }
    if (simbad.result?.error) {
      return (
        <RecommendationError
          message={simbad.result.error}
          onRetry={simbad.refetch}
        />
      );
    }
    if (simbad.objects.length === 0) {
      return (
        <RecommendationInfo testId="simbad-empty">
          {selectedSource
            ? "No hay objetos SIMBAD asociados a la fuente seleccionada."
            : "Ningún objeto SIMBAD coincide con las fuentes detectadas en esta imagen."}
        </RecommendationInfo>
      );
    }
    const matchedIds = selectedSource
      ? new Set(
          simbadObjectsForSource(
            simbad.objects,
            selectedSource.source_id,
            selectedSource.object_type,
          ).map((obj) => obj.main_id),
        )
      : new Set<string>();
    return (
      <div className="relative flex flex-col gap-2 px-2 py-2">
        {showNoMatchToast ? (
          <div className="absolute left-2 right-2 top-1 z-10 rounded-md bg-destructive/90 px-2 py-1 text-center text-xs text-destructive-foreground shadow-sm">
            No se encontró ningún objeto SIMBAD asociado a esta fuente
          </div>
        ) : null}
        {selectedSource ? (
          <div className="flex items-center justify-between gap-2 rounded-md bg-sidebar-accent/50 px-2 py-1">
            <span
              data-testid="simbad-selected-source"
              className="text-xs text-sidebar-accent-foreground"
            >
              Fuente seleccionada:{" "}
              {selectedSource.object_type === "point" ? "puntual" : "extendida"}{" "}
              #{selectedSource.source_id}
            </span>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="h-6 px-2 text-xs"
              onClick={() => {
                setTab("simbad");
                setShowNoMatchToast(false);
              }}
            >
              Ver todas
            </Button>
          </div>
        ) : null}
        <div ref={simbadListRef} className="flex flex-col gap-2">
          {simbad.objects.map((object) => {
            const isMatched =
              matchedIds.size > 0 && matchedIds.has(object.main_id);
            return (
              <div
                key={object.main_id}
                id={`simbad-card-${object.main_id}`}
                className={
                  isMatched
                    ? "rounded-lg ring-2 ring-primary ring-offset-1 ring-offset-sidebar"
                    : undefined
                }
              >
                <SimbadObjectCard
                  object={object}
                  onFocusSource={onFocusSource}
                />
              </div>
            );
          })}
        </div>
      </div>
    );
  }
}

const TAB_TRIGGER_CLASS =
  "flex-none rounded-md px-2 py-1 text-xs font-normal text-muted-foreground shadow-none hover:bg-sidebar-accent/50 data-[state=active]:bg-sidebar-accent data-[state=active]:text-sidebar-accent-foreground data-[state=active]:shadow-none";

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
        <Label
          key={option.value}
          className="inline-flex gap-1 font-normal leading-normal"
        >
          <input
            type="radio"
            name={name}
            value={option.value}
            checked={value === option.value}
            data-testid={`${testIdPrefix}-${option.value}`}
            onChange={() => onSelect(option.value)}
          />
          {option.label}
        </Label>
      ))}
    </fieldset>
  );
}
