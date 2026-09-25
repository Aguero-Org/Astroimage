import { Link } from "@tanstack/react-router";
import { Input } from "@/components/ui/input";

type GlossaryHeaderProps = {
  query: string;
  lastRecordId: string | null;
  onQueryChange: (value: string) => void;
};

export function GlossaryHeader({
  query,
  lastRecordId,
  onQueryChange,
}: Readonly<GlossaryHeaderProps>) {
  return (
    <header
      data-testid="glossary-header"
      className="sticky top-14 z-40 -mx-4 bg-background/95 px-4 py-3 backdrop-blur-sm sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8"
    >
      <div className="mx-auto max-w-2xl lg:mx-0 lg:max-w-3xl">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <h1 className="text-4xl font-semibold tracking-tight">Glosario</h1>
          {lastRecordId && (
            <Link
              to="/image/$recordId"
              params={{ recordId: lastRecordId }}
              data-testid="glossary-back-to-viewer"
              className="text-sm text-muted-foreground hover:text-foreground hover:underline"
            >
              Volver al visor
            </Link>
          )}
        </div>
        <p className="mt-4 text-lg leading-8 text-muted-foreground">
          Las palabras que ves en el visor, escritas como se usan en la
          pantalla. El signo de pregunta al lado de un control es la versión
          corta; acá está el artículo.
        </p>
        <Input
          type="search"
          data-testid="glossary-search"
          aria-label="Buscar en el glosario"
          placeholder="Buscar un concepto…"
          className="mt-6 max-w-md"
          value={query}
          onChange={(event) => {
            onQueryChange(event.target.value);
          }}
        />
      </div>
    </header>
  );
}
