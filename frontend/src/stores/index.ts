import { create } from 'zustand';

interface StoreState {
  token: string | null;
  setToken: (token: string | null) => void;
}

export const useStore = create<StoreState>((set) => ({
  token: localStorage.getItem('token'),
  setToken: (token) => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
    set({ token });
  },
})); 