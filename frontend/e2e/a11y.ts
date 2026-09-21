import AxeBuilder from "@axe-core/playwright";
import { expect, type Page } from "@playwright/test";
import { THEME_STORAGE_KEY, type Theme } from "../src/lib/theme";

export const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag22aa"] as const;

export const THEMES = ["light", "dark"] as const satisfies Theme[];

export async function applyTheme(page: Page, theme: Theme): Promise<void> {
  await page.addInitScript(
    ({ key, value }) => {
      window.localStorage.setItem(key, value);
    },
    { key: THEME_STORAGE_KEY, value: theme },
  );
}

export async function expectNoWcagViolations(
  page: Page,
  options?: { include?: string },
): Promise<void> {
  let builder = new AxeBuilder({ page }).withTags([...WCAG_TAGS]);
  if (options?.include) {
    builder = builder
      .include(options.include)
      .disableRules(["scrollable-region-focusable"]);
  } else {
    builder = builder
      .exclude(".fits-osd")
      .exclude(".openseadragon-canvas")
      .exclude('[id^="fits-osd-nav-"]');
  }
  const results = await builder.analyze();

  const summary = results.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact,
    description: violation.description,
    nodes: violation.nodes.map((node) => node.target),
  }));

  expect(summary, JSON.stringify(summary, null, 2)).toEqual([]);
}
