/**
 * API module index
 * Centralized exports for all API modules
 */

export { apiClient, APIClient } from './client';
export { authAPI } from './auth';
export { tintometryAPI } from './tintometry';

// Re-export all API functions for convenience
export const API = {
  auth: authAPI,
  tintometry: tintometryAPI
};

export default API;