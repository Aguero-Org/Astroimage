import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { apiBaseUrl } from "@/lib/api-client";
import { server } from "@/test/server";
import { EditImageButton } from "./edit-image-dialog";

describe("EditImageButton", () => {
  it("rejects duplicate tags and saves a new title", async () => {
    const user = userEvent.setup();
    let saved: unknown = null;
    server.use(
      http.patch(`${apiBaseUrl()}/image/:recordId`, async ({ request }) => {
        saved = await request.json();
        return HttpResponse.json({ ok: true });
      }),
    );
    const queryClient = new QueryClient({
      defaultOptions: { mutations: { retry: false } },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <EditImageButton
            record={{
              record_id: "11111111-1111-1111-1111-111111111111",
              display_name: "NGC 5128",
              description: "",
              tags: [],
            }}
          />
        </TooltipProvider>
      </QueryClientProvider>,
    );
    await user.click(screen.getByTestId("edit-image"));
    const tags = screen.getByLabelText("Etiquetas", { selector: "input" });
    await user.type(tags, "m31{Enter}");
    await user.type(tags, "M31{Enter}");
    expect(await screen.findByText("Esa etiqueta ya está")).toBeInTheDocument();
    expect(saved).toBeNull();

    await user.clear(tags);
    await user.type(tags, "hubble{Enter}");
    const title = screen.getByLabelText("Título", { selector: "input" });
    await user.clear(title);
    await user.type(title, "NGC editada");
    await user.click(screen.getByTestId("edit-image-save"));
    await waitFor(() => {
      expect(saved).toMatchObject({
        display_name: "NGC editada",
        tags: ["m31", "hubble"],
      });
    });
  });
});
