import { useState } from "react";
import {
  CUSTOM_PRESET_ID,
  matchNamedPreset,
  type NamedPreset,
} from "./named-preset";

type NamedPresetDraftOptions<TParams, TDraft> = {
  presets: readonly NamedPreset<TParams>[];
  defaults: TParams;
  toDraft: (params: TParams) => TDraft;
  parseDraft: (draft: TDraft) => TParams | null;
};

export function useNamedPresetDraft<TParams, TDraft>({
  presets,
  defaults,
  toDraft,
  parseDraft,
}: NamedPresetDraftOptions<TParams, TDraft>) {
  const [draft, setDraft] = useState(() => toDraft(defaults));
  const [presetId, setPresetId] = useState(() =>
    matchNamedPreset(presets, defaults),
  );
  const [lastNamedId, setLastNamedId] = useState(() => {
    const matched = matchNamedPreset(presets, defaults);
    return matched === CUSTOM_PRESET_ID
      ? (presets[0]?.id ?? CUSTOM_PRESET_ID)
      : matched;
  });

  function applyParams(next: TParams) {
    setDraft(toDraft(next));
    const matched = matchNamedPreset(presets, next);
    setPresetId(matched);
    if (matched !== CUSTOM_PRESET_ID) {
      setLastNamedId(matched);
    }
  }

  function applyDraft(next: TDraft) {
    setDraft(next);
    const parsed = parseDraft(next);
    if (parsed === null) {
      setPresetId(CUSTOM_PRESET_ID);
      return;
    }
    const matched = matchNamedPreset(presets, parsed);
    setPresetId(matched);
    if (matched !== CUSTOM_PRESET_ID) {
      setLastNamedId(matched);
    }
  }

  return {
    draft,
    presetId,
    lastNamedId,
    applyParams,
    applyDraft,
    parseDraft: () => parseDraft(draft),
  };
}
