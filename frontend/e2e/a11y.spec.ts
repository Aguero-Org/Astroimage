import { expect, type Page, test } from "@playwright/test";
import { applyTheme, expectNoWcagViolations, THEMES, type Theme } from "./a11y";

async function expectHtmlTheme(page: Page, theme: Theme) {
  const html = page.locator("html");
  if (theme === "dark") {
    await expect(html).toHaveClass(/dark/);
  } else {
    await expect(html).not.toHaveClass(/dark/);
  }
}

async function openHome(page: Page, theme: Theme) {
  await applyTheme(page, theme);
  await page.goto("/");
  await expect(page.getByTestId("home-title")).toBeVisible();
  await expectHtmlTheme(page, theme);
}

async function openImageWithInspector(page: Page, theme: Theme) {
  await applyTheme(page, theme);
  await page.goto("/image/m31");
  await expect(page.getByTestId("inspector-toggle")).toBeVisible();
  await page.getByTestId("inspector-toggle").click();
  await expect(page.getByTestId("inspector-drawer")).toHaveAttribute(
    "data-state",
    "expanded",
  );
  await expectHtmlTheme(page, theme);
}

for (const theme of THEMES) {
  test.describe(`WCAG 2.2 AA (${theme})`, () => {
    test.use({ colorScheme: theme });

    test(`home search and list have no AA violations in ${theme}`, async ({
      page,
    }) => {
      await openHome(page, theme);
      await expect(page.getByTestId("image-list")).toBeVisible();
      await expectNoWcagViolations(page);
    });

    test(`image viewer with inspector open has no AA violations in ${theme}`, async ({
      page,
    }) => {
      await openImageWithInspector(page, theme);
      await expect(page.getByTestId("inspector-section-sources")).toBeVisible();
      await expectNoWcagViolations(page);
      await page.getByTestId("source-preset").click();
      await expect(page.getByTestId("select-content")).toBeVisible();
      await expectNoWcagViolations(page, {
        include: '[data-testid="select-content"]',
      });
    });
  });
}

test("main screens are usable with the keyboard", async ({ page }) => {
  await applyTheme(page, "light");
  await page.goto("/");
  await expect(page.getByTestId("image-list")).toBeVisible();

  await page.getByTestId("search-input").focus();
  await expect(page.getByTestId("search-input")).toBeFocused();
  await page.keyboard.type("M31");

  await page.getByTestId("image-list-item-open").first().focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/image\/.+/);

  await page.getByTestId("inspector-toggle").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("inspector-drawer")).toHaveAttribute(
    "data-state",
    "expanded",
  );

  let inspectorControl = "";
  for (let step = 0; step < 25; step += 1) {
    await page.keyboard.press("Tab");
    inspectorControl = await page.evaluate(
      () =>
        (document.activeElement as HTMLElement | null)?.dataset.testid ?? "",
    );
    if (
      inspectorControl.startsWith("help-") ||
      inspectorControl.startsWith("hdu") ||
      inspectorControl.startsWith("source-") ||
      inspectorControl.startsWith("inspector-section")
    ) {
      break;
    }
  }
  expect(inspectorControl).not.toBe("");
});
