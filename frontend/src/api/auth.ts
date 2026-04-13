import { apiClient } from './client';
import type { AuthResponse, LoginRequest, User } from '@/types';

/**
 * Authentication API module
 * Handles user authentication, token management, and user profile operations
 */

export const authAPI = {
  /**
   * Login user with username/password
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.postData<AuthResponse>('/auth/login/', credentials);
    
    // Store tokens automatically
    apiClient.setAuthToken(response.access);
    
    return response;
  },

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    try {
      // Call logout endpoint if available
      await apiClient.postData('/auth/logout/', {});
    } catch (error) {
      // Continue with local logout even if server call fails
      console.warn('Server logout failed, continuing with local logout');
    } finally {
      // Always clear local token
      apiClient.clearAuthToken();
    }
  },

  /**
   * Refresh authentication token
   */
  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.postData<AuthResponse>('/auth/refresh/', {
      refresh: refreshToken
    });
    
    // Update stored token
    apiClient.setAuthToken(response.access);
    
    return response;
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    return apiClient.getData<User>('/auth/user/');
  },

  /**
   * Update current user profile
   */
  async updateCurrentUser(userData: Partial<User>): Promise<User> {
    return apiClient.patchData<User>('/auth/user/', userData);
  },

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.postData('/auth/password/reset/', { email });
  },

  /**
   * Confirm password reset with token
   */
  async confirmPasswordReset(token: string, newPassword: string): Promise<void> {
    await apiClient.postData('/auth/password/reset/confirm/', {
      token,
      password: newPassword
    });
  },

  /**
   * Change password for authenticated user
   */
  async changePassword(
    oldPassword: string,
    newPassword: string
  ): Promise<void> {
    await apiClient.postData('/auth/password/change/', {
      old_password: oldPassword,
      new_password: newPassword
    });
  },

  /**
   * Verify if user is currently authenticated
   */
  async verifyAuth(): Promise<boolean> {
    try {
      await this.getCurrentUser();
      return true;
    } catch (error) {
      return false;
    }
  }
};

// Export for easier imports
export default authAPI;