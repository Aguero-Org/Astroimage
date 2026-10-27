import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { apiBaseUrl } from "@/lib/api-client";
import { renderWithRouter } from "@/test/router";
import { server } from "@/test/server";

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
    renderWithRouter();
    await waitFor(() => {
      expect(screen.getAllByTestId("edit-image").length).toBeGreaterThan(0);
    });
    await user.click(screen.getAllByTestId("edit-image")[0]);
    const tags = screen.getByLabelText("Etiquetas", { selector: "input" });
    await user.clear(tags);
    await user.type(tags, "m31, M31");
    await user.click(screen.getByTestId("edit-image-save"));
    expect(
      await screen.findByText("Hay etiquetas repetidas"),
    ).toBeInTheDocument();
    expect(saved).toBeNull();

    await user.clear(tags);
    await user.type(tags, "m31, hubble");
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
