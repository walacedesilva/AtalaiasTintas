/**
 * useSalesOverview Hook
 * 
 * React Query hook for fetching sales overview data.
 * Uses dashboard API service with proper caching and refresh intervals.
 */

import { useQuery } from '@tanstack/react-query';
import { getSalesOverview } from '../../services/dashboard';

export const useSalesOverview = () => {
  return useQuery({
    queryKey: ['sales-overview'],
    queryFn: getSalesOverview,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 2 * 60 * 1000, // Refresh every 2 minutes
    refetchOnWindowFocus: true,
    enabled: true // Enabled with mock data
  });
};

export default useSalesOverview;