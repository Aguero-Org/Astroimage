import { z } from "zod";
import { readNumber } from "./source-detection-fields";

export type CrossmatchParams = {
  gaiaRadiusArcsec: number;
  gaiaProbabilityPower: number;
  simbadRadiusArcsec: number;
  simbadProbabilityPower: number;
};

export const DEFAULT_CROSSMATCH_PARAMS: CrossmatchParams = {
  gaiaRadiusArcsec: 5,
  gaiaProbabilityPower: 2,
  simbadRadiusArcsec: 5,
  simbadProbabilityPower: 2,
};

const radiusDraft = z.string().refine((value) => {
  const numeric = readNumber(value);
  return numeric !== null && numeric >= 0 && numeric <= 3600;
});

const powerDraft = z.string().refine((value) => {
  const numeric = readNumber(value);
  return numeric !== null && numeric >= 0.1;
});

export const crossmatchDraftSchema = z.object({
  gaiaRadius: radiusDraft,
  gaiaPower: powerDraft,
  simbadRadius: radiusDraft,
  simbadPower: powerDraft,
});

export type CrossmatchDraft = z.infer<typeof crossmatchDraftSchema>;

export function crossmatchToDraft(params: CrossmatchParams): CrossmatchDraft {
  return {
    gaiaRadius: String(params.gaiaRadiusArcsec),
    gaiaPower: String(params.gaiaProbabilityPower),
    simbadRadius: String(params.simbadRadiusArcsec),
    simbadPower: String(params.simbadProbabilityPower),
  };
}

export function parseCrossmatchDraft(
  draft: CrossmatchDraft,
): CrossmatchParams | null {
  const parsed = crossmatchDraftSchema.safeParse(draft);
  if (!parsed.success) {
    return null;
  }
  return {
    gaiaRadiusArcsec: Number(parsed.data.gaiaRadius),
    gaiaProbabilityPower: Number(parsed.data.gaiaPower),
    simbadRadiusArcsec: Number(parsed.data.simbadRadius),
    simbadProbabilityPower: Number(parsed.data.simbadPower),
  };
}
