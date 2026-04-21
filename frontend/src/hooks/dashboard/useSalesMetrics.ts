/**
 * useSalesMetrics Hook
 * 
 * React Query hook for fetching sales-specific metrics.
 * Uses dashboard services with proper caching.
 */

import { useQuery } from '@tanstack/react-query';
import { getSalesOverview } from '../../services/dashboard';
import type { TimePeriod } from '../../types/dashboard';

export const useSalesMetrics = (timeRange?: TimePeriod) => {
  return useQuery({
    queryKey: ['sales-metrics', timeRange],
    queryFn: getSalesOverview,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 2 * 60 * 1000, // Refresh every 2 minutes
    refetchOnWindowFocus: true,
    enabled: true
  });
};

export const useSalesDashboard = () => {
  return useQuery({
    queryKey: ['sales-dashboard'],
    queryFn: getSalesOverview,
    staleTime: 1 * 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 1 * 60 * 1000, // Refresh every minute
    refetchOnWindowFocus: true,
    enabled: true
  });
};