import { useSyncExternalStore } from "react";
import { readLastImageRecord, subscribeLastImageRecord } from "./last-record";

export function useLastImageRecord() {
  return useSyncExternalStore(
    subscribeLastImageRecord,
    readLastImageRecord,
    () => null,
  );
}
