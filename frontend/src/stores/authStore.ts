/**
 * Zustand auth store for global authentication state management.
 * Supporting feature: User authentication and session persistence.
 */
import { create } from 'zustand';
import { AUTH_BASE_URL } from '../lib/config';

export interface User {
  id: number;
  email: string;
  full_name: string;
  created_at: string;
  last_login: string | null;
}

export interface AuthStore {
  // State
  token: string | null;
  user: User | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Auth methods
  register: (email: string, password: string, fullName: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  // Initial state
  token: null,
  user: null,
  isLoading: false,
  error: null,

  // Simple state setters
  setToken: (token) => set({ token }),
  setUser: (user) => set({ user }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),

  // Register new user
  register: async (email: string, password: string, fullName: string) => {
    const { setLoading, setError, setToken, setUser } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${AUTH_BASE_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // Send cookies
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      const data = await response.json();
      setToken(data.access_token);
      setUser(data.user);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  },

  // Login user
  login: async (email: string, password: string) => {
    const { setLoading, setError, setToken, setUser } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${AUTH_BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // Send/receive cookies
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();
      setToken(data.access_token);
      setUser(data.user);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  },

  // Logout user
  logout: async () => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      await fetch(`${AUTH_BASE_URL}/logout`, {
        method: 'POST',
        credentials: 'include',
      });

      get().clearAuth();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Logout failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  },

  // Fetch current user (restore session from cookie)
  fetchCurrentUser: async () => {
    const { setLoading, setError, setUser, setToken } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${AUTH_BASE_URL}/me`, {
        method: 'GET',
        credentials: 'include', // Include httpOnly cookie
      });

      if (!response.ok) {
        // Not authenticated or token expired
        get().clearAuth();
        return;
      }

      const user = await response.json();
      setUser(user);
      // Token is in httpOnly cookie, no need to set it explicitly
      // But we know we're authenticated if this succeeds
      setToken('authenticated');
    } catch (err) {
      console.error('Failed to fetch current user:', err);
      // Silently fail - means no valid session
      get().clearAuth();
    } finally {
      setLoading(false);
    }
  },

  // Clear authentication state
  clearAuth: () => {
    set({
      token: null,
      user: null,
      error: null,
    });
  },
}));
