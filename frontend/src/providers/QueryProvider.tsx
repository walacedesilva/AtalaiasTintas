import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import React from 'react';
import { ENABLE_DEVTOOLS } from '@/utils/env';

/**
 * React Query client configuration and provider
 * Centralized configuration for all API queries and mutations
 */

// Create query client with optimized defaults
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: (failureCount, error: any) => {
        // Don't retry on auth errors
        if (error?.status_code === 401 || error?.status_code === 403) {
          return false;
        }
        // Retry 3 times for other errors
        return failureCount < 3;
      },
      refetchOnWindowFocus: false, // Prevent excessive API calls
      refetchOnMount: true,
      refetchOnReconnect: true
    },
    mutations: {
      retry: 1, // Retry mutations once on failure
      onError: (error: any) => {
        // Global error handling for mutations
        console.error('Mutation error:', error);
      }
    }
  }
});

interface QueryProviderProps {
  children: React.ReactNode;
}

/**
 * Query client provider component
 * Wraps the app with React Query functionality and devtools
 */
export function QueryProvider({ children }: QueryProviderProps): React.ReactElement {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {ENABLE_DEVTOOLS && (
        <ReactQueryDevtools 
          initialIsOpen={false} 
          position="bottom"
          toggleButtonProps={{
            style: {
              marginLeft: '5px',
              transform: 'scale(0.7)',
              transformOrigin: 'bottom left'
            }
          }}
        />
      )}
    </QueryClientProvider>
  );
}