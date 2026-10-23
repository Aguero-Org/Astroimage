import { catalogHandlers } from "./catalogs";
import { healthHandlers } from "./health";
import { imageHandlers } from "./image";
import { simbadHandlers } from "./simbad";

export const handlers = [
  ...healthHandlers,
  ...imageHandlers,
  ...catalogHandlers,
  ...simbadHandlers,
];
