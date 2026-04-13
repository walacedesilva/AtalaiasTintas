import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authAPI, apiClient } from '@/api';
import type { AuthResponse, LoginRequest, User } from '@/types';

/**
 * Authentication hooks using React Query
 * Provides centralized auth state management with caching and optimistic updates
 */

// Query keys for React Query cache
export const authKeys = {
  all: ['auth'] as const,
  user: () => [...authKeys.all, 'user'] as const,
  profile: (id: number) => [...authKeys.user(), id] as const
};

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

/**
 * Get current authentication state
 */
export function useAuth(): AuthState {
  const { data: user, isLoading, error } = useQuery({
    queryKey: authKeys.user(),
    queryFn: authAPI.getCurrentUser,
    enabled: apiClient.isAuthenticated(), // Only fetch if we have a token
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error: any) => {
      // Don't retry on 401 (unauthorized)
      if (error?.status_code === 401) {
        return false;
      }
      return failureCount < 3;
    }
  });

  return {
    user: user || null,
    isAuthenticated: !!user && !error,
    isLoading
  };
}

/**
 * Login mutation hook
 */
export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: LoginRequest) => authAPI.login(credentials),
    onSuccess: (data: AuthResponse) => {
      // Cache user data immediately
      queryClient.setQueryData(authKeys.user(), data.user);
      
      // Invalidate and refetch any queries that depend on auth
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['user-preferences'] });
    },
    onError: (error) => {
      console.error('Login failed:', error);
      // Clear any cached user data on login failure
      queryClient.setQueryData(authKeys.user(), null);
    }
  });
}

/**
 * Logout mutation hook
 */
export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authAPI.logout,
    onSuccess: () => {
      // Clear all cached data on logout
      queryClient.clear();
    },
    onError: (error) => {
      console.error('Logout error:', error);
      // Still clear cache even if server call failed
      queryClient.clear();
    }
  });
}

/**
 * Update profile mutation hook
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userData: Partial<User>) => authAPI.updateCurrentUser(userData),
    onSuccess: (updatedUser) => {
      // Update cached user data
      queryClient.setQueryData(authKeys.user(), updatedUser);
      
      // Show success notification
      // This will be handled by the UI layer
    },
    onError: (error) => {
      console.error('Profile update failed:', error);
    }
  });
}

/**
 * Change password mutation hook
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: ({ oldPassword, newPassword }: { oldPassword: string; newPassword: string }) =>
      authAPI.changePassword(oldPassword, newPassword),
    onSuccess: () => {
      // Password changed successfully
      // UI will handle success notification
    },
    onError: (error) => {
      console.error('Password change failed:', error);
    }
  });
}

/**
 * Password reset request mutation hook
 */
export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: (email: string) => authAPI.requestPasswordReset(email),
    onSuccess: () => {
      // Reset request sent successfully
    },
    onError: (error) => {
      console.error('Password reset request failed:', error);
    }
  });
}

/**
 * Password reset confirmation mutation hook
 */
export function useConfirmPasswordReset() {
  return useMutation({
    mutationFn: ({ token, newPassword }: { token: string; newPassword: string }) =>
      authAPI.confirmPasswordReset(token, newPassword),
    onSuccess: () => {
      // Password reset successfully
    },
    onError: (error) => {
      console.error('Password reset confirmation failed:', error);
    }
  });
}

/**
 * Auth verification hook for route protection
 */
export function useAuthVerification() {
  return useQuery({
    queryKey: ['auth-verify'],
    queryFn: authAPI.verifyAuth,
    enabled: false, // Only run when explicitly triggered
    retry: false
  });
}

/**
 * Higher-order hook that provides all auth functionality
 */
export function useAuthActions() {
  const login = useLogin();
  const logout = useLogout();
  const updateProfile = useUpdateProfile();
  const changePassword = useChangePassword();
  const requestPasswordReset = useRequestPasswordReset();
  const confirmPasswordReset = useConfirmPasswordReset();

  return {
    login,
    logout,
    updateProfile,
    changePassword,
    requestPasswordReset,
    confirmPasswordReset
  };
}