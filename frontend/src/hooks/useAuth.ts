/**
 * Auth hook for accessing authentication state and methods.
 * Supporting feature: Authentication & session management.
 */
import { useShallow } from 'zustand/react/shallow';
import { useAuthStore } from '../stores/authStore';

export const useAuth = () => {
  return useAuthStore(useShallow((state) => ({
    token: state.token,
    user: state.user,
    isLoading: state.isLoading,
    error: state.error,
    register: state.register,
    login: state.login,
    logout: state.logout,
    fetchCurrentUser: state.fetchCurrentUser,
    clearAuth: state.clearAuth,
    isAuthenticated: state.token !== null,
  })));
};