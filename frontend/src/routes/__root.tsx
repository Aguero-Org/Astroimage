import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createRootRoute, Outlet, useLocation } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { Navbar } from "@/components/navbar";
import { TooltipProvider } from "@/components/ui/tooltip";

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  const location = useLocation();
  const isHome = location.pathname === "/";
  const isImage = location.pathname.startsWith("/image/");
  const showDevtools = import.meta.env.VITE_E2E !== "true";

  return (
    <TooltipProvider delayDuration={200}>
      {!isHome && (
        <div
          className={
            isImage ? "absolute inset-x-0 top-0 z-50" : "sticky top-0 z-50"
          }
        >
          <Navbar />
        </div>
      )}
      <Outlet />
      {showDevtools && (
        <>
          <TanStackRouterDevtools />
          <ReactQueryDevtools buttonPosition="bottom-left" />
        </>
      )}
    </TooltipProvider>
  );
}
