import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { useUiStore } from "@/stores/ui";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);

  return (
    <main className="flex min-h-svh flex-col gap-4 p-6">
      <h1 className="text-2xl font-semibold">astroimage</h1>
      <p className="text-muted-foreground">Frontend toolchain is ready.</p>
      <Button type="button">Sidebar {sidebarOpen ? "open" : "closed"}</Button>
    </main>
  );
}
