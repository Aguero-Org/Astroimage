import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/images/$imageId")({
  component: ImageDetailPage,
});

function ImageDetailPage() {
  const { imageId } = Route.useParams();

  return (
    <main className="flex min-h-svh flex-col gap-4 p-6">
      <h1 className="text-2xl font-semibold">Image {imageId}</h1>
    </main>
  );
}
