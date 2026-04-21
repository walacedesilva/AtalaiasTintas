/**
 * useFiscalStatus Hook
 * 
 * React Query hook for fetching fiscal status and compliance data.
 * Uses dashboard API service with proper caching and refresh intervals.
 */

import { useQuery } from '@tanstack/react-query';
import { getFiscalStatus } from '../../services/dashboard';

export const useFiscalStatus = () => {
  return useQuery({
    queryKey: ['fiscal-status'],
    queryFn: getFiscalStatus,
    staleTime: 5 * 60 * 1000, // 5 minutes  
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    refetchOnWindowFocus: true,
  });
};

export default useFiscalStatus;