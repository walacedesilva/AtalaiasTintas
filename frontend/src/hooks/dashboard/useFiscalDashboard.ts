/**
 * useFiscalDashboard Hook
 * 
 * React Query hook for fetching fiscal dashboard data.
 * Uses dashboard services with proper caching.
 */

import { useQuery } from '@tanstack/react-query';
import { getFiscalDashboard, getComplianceAlerts } from '../../services/dashboard';

export const useFiscalDashboard = () => {
  return useQuery({
    queryKey: ['fiscal-dashboard'],
    queryFn: getFiscalDashboard,
    staleTime: 3 * 60 * 1000, // 3 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes  
    refetchInterval: 3 * 60 * 1000, // Refresh every 3 minutes
    refetchOnWindowFocus: true,
    enabled: true
  });
};

export const useComplianceAlerts = () => {
  return useQuery({
    queryKey: ['compliance-alerts'],
    queryFn: getComplianceAlerts,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    refetchOnWindowFocus: true,
    enabled: true
  });
};