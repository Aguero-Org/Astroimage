import { createFileRoute } from "@tanstack/react-router";
import { type ReactNode, useEffect, useState } from "react";
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

function RecordsSection(
  props: Readonly<{
    filter: string;
    onFilterChange: (value: string) => void;
    selectedRecord: string | null;
    onSelect: (recordId: string) => void;
  }>,
) {
  const listQuery = useListHubbleImages(
    props.filter ? { cuerpo_celeste: props.filter } : undefined,
  );

  let records: ReactNode;
  if (listQuery.isLoading) {
    records = <p>Loading…</p>;
  } else if (listQuery.isError) {
    records = <p className="text-destructive">{String(listQuery.error)}</p>;
  } else if (listQuery.data?.status === 200) {
    records = (
      <ul className="list-disc pl-6">
        {listQuery.data.data.records.map(
          (record: { record_id: string; name: string }) => (
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
          ),
        )}
      </ul>
    );
  } else {
    records = null;
  }

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-medium">FITS records in database</h2>
      <label className="flex items-center gap-2">
        <span>Filter by name</span>
        <input
          className="rounded border px-2 py-1"
          value={props.filter}
          onChange={(event) => props.onFilterChange(event.target.value)}
        />
      </label>
      {records}
    </section>
  );
}

function HduSection(
  props: Readonly<{
    recordId: string | null;
    selectedHdu: number | null;
    onSelectHdu: (hdu: number | null) => void;
  }>,
) {
  const metadataQuery = useGetImageInfo(props.recordId ?? "", {
    query: { enabled: props.recordId !== null },
  });

  if (props.recordId === null) {
    return null;
  }

  let hdus: ReactNode;
  if (metadataQuery.isLoading) {
    hdus = <p>Loading…</p>;
  } else if (metadataQuery.isError) {
    hdus = <p className="text-destructive">{String(metadataQuery.error)}</p>;
  } else if (metadataQuery.data?.status === 200) {
    hdus = (
      <ul className="flex flex-wrap gap-2">
        {metadataQuery.data.data.hdus.images?.map(
          (hdu: {
            index: number;
            kind?: string | null;
            shape?: number[] | null;
          }) => (
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
          ),
        )}
      </ul>
    );
  } else {
    hdus = null;
  }

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-medium">Image HDUs</h2>
      {hdus}
    </section>
  );
}

function FetchSection(
  props: Readonly<{
    query: string;
    onQueryChange: (value: string) => void;
    onSubmit: (value: string) => void;
    submittedQuery: string;
  }>,
) {
  const fetchQuery = useFetchHubbleImage(
    { query: props.submittedQuery },
    { query: { enabled: props.submittedQuery !== "" } },
  );

  let result: ReactNode;
  if (props.submittedQuery === "") {
    result = null;
  } else if (fetchQuery.isLoading) {
    result = <p>Fetching…</p>;
  } else if (fetchQuery.isError) {
    result = <p className="text-destructive">{String(fetchQuery.error)}</p>;
  } else if (fetchQuery.data?.status === 200) {
    result = (
      <p>
        record_id: <code>{fetchQuery.data.data.record_id}</code>
      </p>
    );
  } else {
    result = null;
  }

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
      {result}
    </section>
  );
}
