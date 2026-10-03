import { expect, test } from "@playwright/test";

test("home glossary link opens the glossary", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("home-glossary").click();
  await expect(page).toHaveURL(/\/glossary/);
  await expect(page.getByTestId("glossary-page")).toBeVisible();
  await expect(page.getByTestId("glossary-entry-fwhm")).toBeVisible();
});

test("viewer help book opens the matching glossary entry", async ({ page }) => {
  await page.goto("/image/m31");
  await page.getByTestId("inspector-toggle").click();
  await expect(page.getByTestId("source-help-fwhm-glossary")).toBeVisible();
  await page.getByTestId("source-help-fwhm-glossary").click();
  await expect(page).toHaveURL(/\/glossary#fwhm/);
  await expect(page.getByTestId("glossary-entry-fwhm")).toBeVisible();
  await expect(page.getByTestId("glossary-back-to-viewer")).toBeVisible();
});
