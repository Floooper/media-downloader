import create from 'zustand';

interface Toast {
  id: string;
  type: 'default' | 'success' | 'warning' | 'error';
  title?: string;
  message: string;
}

interface UIState {
  // Theme
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  
  // Sidebar
  isSidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  
  // Loading states
  isLoading: boolean;
  loadingMessage: string | null;
  setLoading: (loading: boolean, message?: string | null) => void;
  
  // Toasts
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  
  // Modal
  isModalOpen: boolean;
  modalContent: React.ReactNode | null;
  openModal: (content: React.ReactNode) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  // Theme
  isDarkMode: false,
  toggleDarkMode: () => set((state) => ({ isDarkMode: !state.isDarkMode })),
  
  // Sidebar
  isSidebarOpen: false,
  setSidebarOpen: (open) => set({ isSidebarOpen: open }),
  
  // Loading states
  isLoading: false,
  loadingMessage: null,
  setLoading: (loading, message = null) => 
    set({ isLoading: loading, loadingMessage: message }),
  
  // Toasts
  toasts: [],
  addToast: (toast) =>
    set((state) => ({
      toasts: [
        ...state.toasts,
        { ...toast, id: Math.random().toString(36).substr(2, 9) },
      ],
    })),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((toast) => toast.id !== id),
    })),
  
  // Modal
  isModalOpen: false,
  modalContent: null,
  openModal: (content) => set({ isModalOpen: true, modalContent: content }),
  closeModal: () => set({ isModalOpen: false, modalContent: null }),
}));

// Toast helper functions
export const toast = {
  show: (message: string) =>
    useUIStore.getState().addToast({ type: 'default', message }),
  success: (message: string, title?: string) =>
    useUIStore.getState().addToast({ type: 'success', title, message }),
  warning: (message: string, title?: string) =>
    useUIStore.getState().addToast({ type: 'warning', title, message }),
  error: (message: string, title?: string) =>
    useUIStore.getState().addToast({ type: 'error', title, message }),
};

// Loading helper functions
export const loading = {
  show: (message?: string) => useUIStore.getState().setLoading(true, message),
  hide: () => useUIStore.getState().setLoading(false),
};

// Modal helper functions
export const modal = {
  show: (content: React.ReactNode) => useUIStore.getState().openModal(content),
  hide: () => useUIStore.getState().closeModal(),
};
