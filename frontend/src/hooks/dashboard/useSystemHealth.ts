/**
 * useSystemHealth Hook
 * 
 * React Query hook for fetching system health and monitoring data.
 * Uses dashboard API service with proper caching and refresh intervals.
 */

import { useQuery } from '@tanstack/react-query';
import { getSystemHealth } from '../../services/dashboard';

export const useSystemHealth = () => {
  return useQuery({
    queryKey: ['system-health'],
    queryFn: getSystemHealth,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
    refetchOnWindowFocus: true,
  });
};