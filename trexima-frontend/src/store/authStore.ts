/**
 * TREXIMA v4.0 - Auth Store
 *
 * Zustand store for authentication state management.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, AuthConfig } from '../types';
import authApi from '../api/auth';

interface AuthState {
  user: User | null;
  config: AuthConfig | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: () => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<boolean>;
  fetchUser: () => Promise<void>;
  fetchConfig: () => Promise<void>;
  updateProfile: (data: { display_name?: string }) => Promise<void>;
  clearError: () => void;

  // Dev mode
  devLogin: (userId?: string) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      config: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async () => {
        const config = get().config;
        if (config?.login_url) {
          window.location.href = config.login_url;
        }
      },

      logout: async () => {
        set({ isLoading: true, error: null });
        try {
          const result = await authApi.logout();
          set({ user: null, isAuthenticated: false });
          localStorage.removeItem('auth_token');

          if (result.redirect_url) {
            window.location.href = result.redirect_url;
          }
        } catch (error) {
          set({ error: 'Logout failed' });
        } finally {
          set({ isLoading: false });
        }
      },

      checkAuth: async () => {
        set({ isLoading: true, error: null });
        try {
          const result = await authApi.checkAuth();
          set({
            isAuthenticated: result.authenticated,
            user: result.user || null,
          });
          return result.authenticated;
        } catch (error) {
          set({ isAuthenticated: false, user: null });
          return false;
        } finally {
          set({ isLoading: false });
        }
      },

      fetchUser: async () => {
        set({ isLoading: true, error: null });
        try {
          const user = await authApi.getCurrentUser();
          set({ user, isAuthenticated: true });
        } catch (error) {
          set({ error: 'Failed to fetch user' });
        } finally {
          set({ isLoading: false });
        }
      },

      fetchConfig: async () => {
        try {
          const config = await authApi.getConfig();
          set({ config });
        } catch (error) {
          console.error('Failed to fetch auth config:', error);
        }
      },

      updateProfile: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const user = await authApi.updateProfile(data);
          set({ user });
        } catch (error) {
          set({ error: 'Failed to update profile' });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      clearError: () => set({ error: null }),

      // Development mode login
      devLogin: async (userId?: string) => {
        set({ isLoading: true, error: null });
        try {
          const result = await authApi.dev.getToken(userId);
          localStorage.setItem('auth_token', result.token);
          set({ user: result.user, isAuthenticated: true });
        } catch (error) {
          set({ error: 'Dev login failed' });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'trexima-auth',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useAuthStore;
