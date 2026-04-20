/**
 * useBusinessMetrics Hook
 * 
 * React Query hook for fetching business metrics data.
 * Uses dashboard API service with proper caching and refresh intervals.
 */

import { useQuery } from '@tanstack/react-query';
import { getBusinessMetrics } from '../../services/dashboard';
import type { TimePeriod } from '../../types/dashboard';

export const useBusinessMetrics = (timeRange: TimePeriod = 'today') => {
  return useQuery({
    queryKey: ['business-metrics', timeRange],
    queryFn: () => getBusinessMetrics({ timeRange }),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 30 * 1000, // 30 seconds
    retry: 3,
    enabled: true // Enabled with mock data
  });
};

export default useBusinessMetrics;