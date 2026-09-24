import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CUSTOM_PRESET_ID, type NamedPreset } from "./named-preset";
import { useNamedPresetDraft } from "./use-named-preset-draft";

type Params = { n: number };
type Draft = { n: string };

const PRESETS: NamedPreset<Params>[] = [
  {
    id: "equilibrio",
    label: "Equilibrio",
    outcome: "ok",
    hint: "ok",
    values: { n: 1 },
  },
  {
    id: "alto",
    label: "Alto",
    outcome: "más",
    hint: "más",
    values: { n: 9 },
  },
];

function setup() {
  return renderHook(() =>
    useNamedPresetDraft<Params, Draft>({
      presets: PRESETS,
      defaults: { n: 1 },
      toDraft: (params) => ({ n: String(params.n) }),
      parseDraft: (draft) => {
        if (draft.n.trim() === "") {
          return null;
        }
        const n = Number(draft.n);
        return Number.isFinite(n) ? { n } : null;
      },
    }),
  );
}

describe("useNamedPresetDraft", () => {
  it("starts on the default named preset", () => {
    const { result } = setup();
    expect(result.current.presetId).toBe("equilibrio");
    expect(result.current.draft).toEqual({ n: "1" });
  });

  it("marks custom when the draft cannot be parsed", () => {
    const { result } = setup();
    act(() => {
      result.current.applyDraft({ n: "" });
    });
    expect(result.current.presetId).toBe(CUSTOM_PRESET_ID);
    expect(result.current.parseDraft()).toBeNull();
  });

  it("applies another named preset", () => {
    const { result } = setup();
    act(() => {
      result.current.applyParams({ n: 9 });
    });
    expect(result.current.presetId).toBe("alto");
    expect(result.current.lastNamedId).toBe("alto");
    expect(result.current.draft).toEqual({ n: "9" });
  });
});
