import { create } from "zustand";

type TransfersState = {
  transferIds: string[];
  add: (transferId: string) => void;
  remove: (transferId: string) => void;
};

export const useTransfersStore = create<TransfersState>((set) => ({
  transferIds: [],
  add: (transferId) => {
    set((state) =>
      state.transferIds.includes(transferId)
        ? state
        : { transferIds: [...state.transferIds, transferId] },
    );
  },
  remove: (transferId) => {
    set((state) => ({
      transferIds: state.transferIds.filter((id) => id !== transferId),
    }));
  },
}));
