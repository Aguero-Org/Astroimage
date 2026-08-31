import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  useFetchHubbleImage,
  useGetImageInfo,
  useListHubbleImages,
} from "@/api/generated/hub/hub";
import { useRenderFitsImage } from "@/api/generated/render/render";
import { Button } from "@/components/ui/button";
import { useUiStore } from "@/stores/ui";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);
  const [filter, setFilter] = useState("");
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [selectedRecord, setSelectedRecord] = useState<string | null>(null);
  const [selectedHdu, setSelectedHdu] = useState<number | null>(null);

  const objectUrl = useRenderedImage(selectedRecord, selectedHdu);

  return (
    <main className="flex min-h-svh flex-col gap-4 p-6">
      <h1 className="text-2xl font-semibold">astroimage</h1>
      <Button type="button">Sidebar {sidebarOpen ? "open" : "closed"}</Button>

      <RecordsSection
        filter={filter}
        onFilterChange={setFilter}
        selectedRecord={selectedRecord}
        onSelect={(recordId) => {
          setSelectedRecord(recordId);
          setSelectedHdu(null);
        }}
      />

      <HduSection
        recordId={selectedRecord}
        selectedHdu={selectedHdu}
        onSelectHdu={setSelectedHdu}
      />

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-medium">Render</h2>
        {objectUrl ? (
          <img
            src={objectUrl}
            alt="rendered FITS"
            className="max-w-full rounded border"
          />
        ) : (
          <p className="text-muted-foreground">
            {selectedHdu === null
              ? "Select a record to render the default HDU."
              : "Loading image…"}
          </p>
        )}
      </section>

      <FetchSection
        query={query}
        onQueryChange={setQuery}
        onSubmit={setSubmittedQuery}
        submittedQuery={submittedQuery}
      />
    </main>
  );
}

function useRenderedImage(
  recordId: string | null,
  hdu: number | null,
): string | undefined {
  const renderQuery = useRenderFitsImage(
    recordId ?? "",
    { hdu: hdu ?? undefined },
    { query: { enabled: recordId !== null } },
  );
  const blob = renderQuery.data?.data as Blob | undefined;
  const [objectUrl, setObjectUrl] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (!blob) {
      setObjectUrl(undefined);
      return;
    }
    const url = URL.createObjectURL(blob);
    setObjectUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [blob]);

  return objectUrl;
}

function RecordsSection(props: {
  filter: string;
  onFilterChange: (value: string) => void;
  selectedRecord: string | null;
  onSelect: (recordId: string) => void;
}) {
  const listQuery = useListHubbleImages(
    props.filter ? { cuerpo_celeste: props.filter } : undefined,
  );

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-medium">FITS records in database</h2>
      <label className="flex items-center gap-2">
        Filter by name
        <input
          className="rounded border px-2 py-1"
          value={props.filter}
          onChange={(event) => props.onFilterChange(event.target.value)}
        />
      </label>
      {listQuery.isLoading ? (
        <p>Loading…</p>
      ) : listQuery.isError ? (
        <p className="text-destructive">{String(listQuery.error)}</p>
      ) : (
        <ul className="list-disc pl-6">
          {listQuery.data?.data.records.map((record) => (
            <li key={record.record_id}>
              <button
                type="button"
                className={
                  record.record_id === props.selectedRecord
                    ? "font-semibold underline"
                    : undefined
                }
                onClick={() => props.onSelect(record.record_id)}
              >
                <code>{record.record_id}</code> — {record.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function HduSection(props: {
  recordId: string | null;
  selectedHdu: number | null;
  onSelectHdu: (hdu: number | null) => void;
}) {
  const metadataQuery = useGetImageInfo(props.recordId ?? "", {
    query: { enabled: props.recordId !== null },
  });

  if (props.recordId === null) {
    return null;
  }

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-medium">Image HDUs</h2>
      {metadataQuery.isLoading ? (
        <p>Loading…</p>
      ) : metadataQuery.isError ? (
        <p className="text-destructive">{String(metadataQuery.error)}</p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {metadataQuery.data?.data.hdus.images?.map((hdu) => (
            <li key={hdu.index}>
              <button
                type="button"
                className={
                  hdu.index === props.selectedHdu
                    ? "rounded border px-2 py-1 font-semibold"
                    : "rounded border px-2 py-1"
                }
                onClick={() => props.onSelectHdu(hdu.index)}
              >
                <code>#{hdu.index}</code> {hdu.kind ?? "image"} —{" "}
                {hdu.shape ? `${hdu.shape[1]}×${hdu.shape[0]}` : "no data"}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function FetchSection(props: {
  query: string;
  onQueryChange: (value: string) => void;
  onSubmit: (value: string) => void;
  submittedQuery: string;
}) {
  const fetchQuery = useFetchHubbleImage(
    { query: props.submittedQuery },
    { query: { enabled: props.submittedQuery !== "" } },
  );

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-medium">Fetch from Hubble</h2>
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          props.onSubmit(props.query);
        }}
      >
        <input
          className="rounded border px-2 py-1"
          value={props.query}
          onChange={(event) => props.onQueryChange(event.target.value)}
          placeholder="celestial body (e.g. M31)"
        />
        <Button type="submit">Fetch</Button>
      </form>
      {props.submittedQuery !== "" &&
        (fetchQuery.isLoading ? (
          <p>Fetching…</p>
        ) : fetchQuery.isError ? (
          <p className="text-destructive">{String(fetchQuery.error)}</p>
        ) : (
          <p>
            record_id: <code>{fetchQuery.data?.data.record_id}</code>
          </p>
        ))}
    </section>
  );
}
