import { useReducer } from "react";
import {
  DEFAULT_IMAGE_WORKSPACE,
  imageWorkspaceReducer,
} from "./image-workspace";

export function useImageWorkspace() {
  return useReducer(imageWorkspaceReducer, DEFAULT_IMAGE_WORKSPACE);
}
