import { expect, test } from "@playwright/test";

test("home glossary link opens the glossary", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("home-glossary").click();
  await expect(page).toHaveURL(/\/glossary/);
  await expect(page.getByTestId("glossary-page")).toBeVisible();
  await expect(page.getByTestId("glossary-entry-fwhm")).toBeVisible();
});

test("scroll spy centers the active toc entry and updates the title", async ({
  page,
}) => {
  await page.goto("/glossary");
  await expect(page.getByTestId("glossary-page")).toBeVisible();

  const nav = page.getByTestId("glossary-toc");
  const active = nav.locator('ol ol a[data-active="true"]').first();

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
  await expect(active).toBeVisible();

  const navBox = await nav.boundingBox();
  const activeBox = await active.boundingBox();
  expect(navBox).not.toBeNull();
  expect(activeBox).not.toBeNull();
  if (navBox && activeBox) {
    const activeCenter = activeBox.y + activeBox.height / 2;
    const navCenter = navBox.y + navBox.height / 2;
    expect(Math.abs(activeCenter - navCenter)).toBeLessThan(40);
  }

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await expect(page).toHaveTitle(`${await active.textContent()} - Astroimage`);
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
