import { healthHandlers } from "./health";
import { imageHandlers } from "./image";

export const handlers = [...healthHandlers, ...imageHandlers];
