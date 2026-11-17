export function settle(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      window.setTimeout(resolve, 250);
    });
  });
}

function findClickable(selector: string): HTMLElement | null {
  return document.querySelector<HTMLElement>(selector);
}

async function expandPanel(toggleTestId: string): Promise<void> {
  const toggle = findClickable(`[data-testid="${toggleTestId}"]`);
  if (!toggle || toggle.getAttribute("aria-expanded") === "true") {
    return;
  }
  toggle.click();
  await settle();
}

export function openInspector(): Promise<void> {
  return expandPanel("inspector-toggle");
}

export function openScientific(): Promise<void> {
  return expandPanel("scientific-toggle");
}

export async function focusScientificTab(tabTestId: string): Promise<void> {
  await openScientific();
  findClickable(`[data-testid="${tabTestId}"]`)?.click();
  await settle();
}

export async function selectFirstSource(): Promise<void> {
  if (findClickable('[data-testid="source-selection"]')) {
    return;
  }
  findClickable('[data-testid="source-marker"]')?.click();
  await settle();
}
