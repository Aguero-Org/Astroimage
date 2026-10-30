import { useLastRecordStore } from "./last-record";

export function useLastImageRecord() {
  return useLastRecordStore((state) => state.record);
}
