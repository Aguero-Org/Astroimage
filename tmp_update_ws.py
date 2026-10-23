import sys

path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'useSimbadReferences' not in content:
    content = content.replace(
        'import { useCatalogRecommendations } from "../use-catalog-recommendations";\n',
        'import { useCatalogRecommendations } from "../use-catalog-recommendations";\nimport { useSimbadReferences } from "../use-simbad-references";\nimport { SimbadObjectCard } from "./simbad-object-card";\nimport { simbadObjectsForSource } from "../simbad-references";\n',
    )

content = content.replace(
    '''type ScientificWorkspaceProps = {
  recordId: string;
  enabled: boolean;
  params: RecommendCatalogsParams | undefined;
  image: ReactNode;
  preview?: string;
};''',
    '''type ScientificWorkspaceProps = {
  recordId: string;
  enabled: boolean;
  params: RecommendCatalogsParams | undefined;
  image: ReactNode;
  preview?: string;
  hdu?: number | null;
  selectedSource?: {
    source_id: number;
    object_type: "point" | "extended";
  } | null;
  onFocusSource?: (sourceId: number, objectType: "point" | "extended") => void;
};''',
)

content = content.replace(
    '''export function ScientificWorkspace({
  recordId,
  enabled,
  params,
  preview,
  image,
}: Readonly<ScientificWorkspaceProps>) {''',
    '''export function ScientificWorkspace({
  recordId,
  enabled,
  params,
  preview,
  image,
  hdu = null,
  selectedSource,
  onFocusSource,
}: Readonly<ScientificWorkspaceProps>) {''',
)

content = content.replace(
    '''      <ScientificSidebar
        recordId={recordId}
        enabled={enabled}
        params={params}
        preview={preview}
        onResizeStart={startResize}
      />''',
    '''      <ScientificSidebar
        recordId={recordId}
        enabled={enabled}
        params={params}
        preview={preview}
        hdu={hdu}
        selectedSource={selectedSource}
        onFocusSource={onFocusSource}
        onResizeStart={startResize}
      />''',
)

content = content.replace(
    '''type ScientificSidebarProps = {
  recordId: string;
  enabled: boolean;
  params: RecommendCatalogsParams | undefined;
  preview: string | undefined;
  onResizeStart: (event: ReactPointerEvent<HTMLButtonElement>) => void;
};''',
    '''type ScientificSidebarProps = {
  recordId: string;
  enabled: boolean;
  params: RecommendCatalogsParams | undefined;
  preview: string | undefined;
  hdu: number | null;
  selectedSource?: {
    source_id: number;
    object_type: "point" | "extended";
  } | null;
  onFocusSource?: (sourceId: number, objectType: "point" | "extended") => void;
  onResizeStart: (event: ReactPointerEvent<HTMLButtonElement>) => void;
};''',
)

content = content.replace(
    '''function ScientificSidebar({
  recordId,
  enabled,
  params,
  preview,
  onResizeStart,
}: Readonly<ScientificSidebarProps>) {''',
    '''function ScientificSidebar({
  recordId,
  enabled,
  params,
  preview,
  hdu,
  selectedSource,
  onFocusSource,
  onResizeStart,
}: Readonly<ScientificSidebarProps>) {''',
)

if "useSimbadReferences" not in content.split("function ScientificSidebar")[1].split("const [tab")[0]:
    content = content.replace(
        '''  const {
    result,
    publications,
    isLoading,
    isFetching,
    isError,
    errorMessage,
    refetch,
  } = useCatalogRecommendations({ recordId, enabled, params });
  const [tab, setTab] = useState<"catalogs" | "papers">("catalogs");''',
        '''  const {
    result,
    publications,
    isLoading,
    isFetching,
    isError,
    errorMessage,
    refetch,
  } = useCatalogRecommendations({ recordId, enabled, params });
  const simbad = useSimbadReferences({
    recordId,
    hdu: hdu ?? null,
    enabled,
  });
  const [tab, setTab] = useState<"catalogs" | "papers" | "simbad">("catalogs");
  useEffect(() => {
    if (enabled && selectedSource) {
      setTab("simbad");
    }
  }, [enabled, selectedSource]);''',
    )

content = content.replace(
    '  const activeCount = tab === "catalogs" ? items.length : publications.length;',
    '  const activeCount =\n    tab === "catalogs"\n      ? items.length\n      : tab === "papers"\n        ? publications.length\n        : simbad.objects.length;',
)

content = content.replace(
    '''        <div
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
        </div>''',
    '''        <div
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
          <TabButton
            id="simbad"
            label={`SIMBAD (${simbad.objects.length})`}
            active={tab === "simbad"}
            onSelect={() => setTab("simbad")}
          />
        </div>''',
)

content = content.replace(
    '''        <p
          data-testid="scientific-explainer"
          className="px-2 pt-2 text-[11px] text-muted-foreground"
        >
          {tab === "catalogs"
            ? "Un catálogo es una tabla de fuentes del cielo (estrellas, galaxias, etc.) con sus posiciones y propiedades. Se listan los que cubren esta imagen."
            : "Una publicación es un trabajo científico sobre los datos. Se listan los artículos de cada catálogo y las referencias de su documentación."}
        </p>''',
    '''        <p
          data-testid="scientific-explainer"
          className="px-2 pt-2 text-[11px] text-muted-foreground"
        >
          {tab === "catalogs"
            ? "Un catálogo es una tabla de fuentes del cielo (estrellas, galaxias, etc.) con sus posiciones y propiedades. Se listan los que cubren esta imagen."
            : tab === "papers"
              ? "Una publicación es un trabajo científico sobre los datos. Se listan los artículos de cada catálogo y las referencias de su documentación."
              : "SIMBAD reúne objetos astronómicos identificados, sus alias, propiedades y bibliografía. Se muestran los objetos que coinciden con las fuentes detectadas en esta imagen."}
        </p>''',
)

content = content.replace(
    '  const showControls = activeCount >= 2;',
    '  const showControls = tab !== "simbad" && activeCount >= 2;',
)

if "simbad.isError" not in content:
    old = '''    if (tab === "catalogs") {
      return (
        <CatalogList
          items={items}
          matches={catalogues}
          radiusArcsec={result.radius_arcsec}
        />
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
    return <PublicationList items={papers} />;
  }
}'''
    new = '''    if (tab === "catalogs") {
      return (
        <CatalogList
          items={items}
          matches={catalogues}
          radiusArcsec={result.radius_arcsec}
        />
      );
    }
    if (tab === "papers") {
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
      return <PublicationList items={papers} />;
    }
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
    const matchedObjects = selectedSource
      ? simbadObjectsForSource(
          simbad.objects,
          selectedSource.source_id,
          selectedSource.object_type,
        )
      : simbad.objects;
    if (matchedObjects.length === 0) {
      return (
        <RecommendationInfo testId="simbad-empty">
          {selectedSource
            ? "No hay objetos SIMBAD asociados a la fuente seleccionada."
            : "No se encontraron objetos SIMBAD para esta imagen."}
        </RecommendationInfo>
      );
    }
    return (
      <div className="flex flex-col gap-2 px-2 py-2">
        {selectedSource ? (
          <div
            data-testid="simbad-selected-source"
            className="rounded-md bg-sidebar-accent/50 px-2 py-1 text-xs text-sidebar-accent-foreground"
          >
            Fuente seleccionada: {selectedSource.object_type === "point" ? "puntual" : "extendida"} #
            {selectedSource.source_id}
          </div>
        ) : null}
        {matchedObjects.map((object) => (
          <SimbadObjectCard
            key={object.main_id}
            object={object}
            onFocusSource={onFocusSource}
          />
        ))}
      </div>
    );
  }
}'''
    content = content.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('done')
