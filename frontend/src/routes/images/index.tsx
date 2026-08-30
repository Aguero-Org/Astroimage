import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/images/")({
  component: ImagesPage,
});

function ImagesPage() {
  return (
    <main className="flex min-h-svh flex-col gap-4 p-6">
      <h1 className="text-2xl font-semibold">Images</h1>
    </main>
  );
}
