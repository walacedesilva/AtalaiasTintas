/**
 * useMonitoring Hooks
 * 
 * React Query hooks for fetching monitoring and system health data.
 * Uses mock monitoring services with appropriate caching strategies.
 */

import { useQuery } from '@tanstack/react-query';

// Mock monitoring functions
const getSystemHealth = async () => {
  await new Promise(resolve => setTimeout(resolve, 300));
  return {
    status: 'healthy',
    uptime: Math.floor(Math.random() * 100000),
    cpu: Math.floor(Math.random() * 30) + 20,
    memory: Math.floor(Math.random() * 40) + 30,
    disk: Math.floor(Math.random() * 20) + 10,
  };
};

const getPerformanceMetrics = async () => {
  await new Promise(resolve => setTimeout(resolve, 400));
  return {
    responseTime: Math.floor(Math.random() * 200) + 100,
    throughput: Math.floor(Math.random() * 1000) + 500,
    errorRate: Math.random() * 0.05,
    availability: 99.9 + Math.random() * 0.1,
  };
};

const getServiceStatus = async () => {
  await new Promise(resolve => setTimeout(resolve, 200));
  return {
    api: 'online',
    database: 'online',
    cache: 'online',
    storage: 'online',
  };
};

const getActiveUsers = async () => {
  await new Promise(resolve => setTimeout(resolve, 250));
  return {
    current: Math.floor(Math.random() * 50) + 10,
    peak: Math.floor(Math.random() * 100) + 50,
    total: Math.floor(Math.random() * 500) + 200,
  };
};

export const useSystemMonitoring = () => {
  return useQuery({
    queryKey: ['system-monitoring'],
    queryFn: getSystemHealth,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
    refetchOnWindowFocus: true,
    enabled: true
  });
};

export const usePerformanceMetrics = () => {
  return useQuery({
    queryKey: ['performance-metrics'],
    queryFn: getPerformanceMetrics,
    staleTime: 1 * 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 1 * 60 * 1000, // Refresh every minute
    refetchOnWindowFocus: true,
    enabled: true
  });
};

export const useServiceStatus = () => {
  return useQuery({
    queryKey: ['service-status'],
    queryFn: getServiceStatus,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 2 * 60 * 1000, // Refresh every 2 minutes
    refetchOnWindowFocus: true,
    enabled: true
  });
};

export const useActiveUsers = () => {
  return useQuery({
    queryKey: ['active-users'],
    queryFn: getActiveUsers,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    refetchOnWindowFocus: true,
    enabled: true
  });
};