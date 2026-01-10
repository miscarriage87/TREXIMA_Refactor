/**
 * TREXIMA v2.0 - Authentication API
 */

import apiClient from './client';
import type { User, AuthConfig } from '../types';

export const authApi = {
  /**
   * Get current user information
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<{ user: User }>('/auth/user');
    return response.data.user;
  },

  /**
   * Get auth configuration (login URLs, etc.)
   */
  getConfig: async (): Promise<AuthConfig> => {
    const response = await apiClient.get<{ config: AuthConfig }>('/auth/config');
    return response.data.config;
  },

  /**
   * Check if user is authenticated
   */
  checkAuth: async (): Promise<{ authenticated: boolean; user?: User }> => {
    const response = await apiClient.get('/auth/check');
    return response.data;
  },

  /**
   * Logout user
   */
  logout: async (): Promise<{ redirect_url?: string }> => {
    const response = await apiClient.post('/auth/logout');
    return response.data;
  },

  /**
   * Update user profile
   */
  updateProfile: async (data: { display_name?: string }): Promise<User> => {
    const response = await apiClient.put<{ user: User }>('/auth/profile', data);
    return response.data.user;
  },

  // Development-only endpoints
  dev: {
    /**
     * Get development token (dev mode only)
     */
    getToken: async (userId?: string): Promise<{ token: string; user: User }> => {
      const response = await apiClient.post('/auth/dev/token', { user_id: userId });
      return response.data;
    },

    /**
     * List development users (dev mode only)
     */
    listUsers: async (): Promise<User[]> => {
      const response = await apiClient.get<{ users: User[] }>('/auth/dev/users');
      return response.data.users;
    },
  },
};

export default authApi;
