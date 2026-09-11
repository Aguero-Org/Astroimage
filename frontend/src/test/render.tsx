import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
}

export function renderHookWithQuery<TResult>(hook: () => TResult): {
  result: { current: TResult };
} {
  const queryClient = createTestQueryClient();
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  return renderHook(hook, { wrapper });
}
