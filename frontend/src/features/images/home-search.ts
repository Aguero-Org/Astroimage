import { z } from "zod";
import type { RecordSortField } from "./api";
import type { CandidateSortField } from "./candidate-api";

const recordSortFields = [
  "product_filename",
  "instrument",
  "proposal_id",
  "filters",
  "size_bytes",
  "observed_at",
  "display_name",
  "created_at",
] as const satisfies readonly RecordSortField[];

const candidateSortFields = [
  "product_filename",
  "instrument",
  "proposal_id",
  "filters",
  "size_bytes",
  "observed_at",
] as const satisfies readonly CandidateSortField[];

export const homeSearchSchema = z.object({
  query: z.string().default("").catch(""),
  page: z.coerce.number().int().min(1).catch(1),
  sort: z.enum(recordSortFields).catch("created_at"),
  order: z.enum(["asc", "desc"]).catch("desc"),
  cpage: z.coerce.number().int().min(1).catch(1),
  csort: z.enum(candidateSortFields).catch("product_filename"),
  corder: z.enum(["asc", "desc"]).catch("asc"),
});

export type HomeSearch = z.infer<typeof homeSearchSchema>;
