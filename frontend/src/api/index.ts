/**
 * API module index
 * Centralized exports for all API modules
 */

export { apiClient, APIClient } from './client';

import { authAPI } from './auth';
import { tintometryAPI } from './tintometry';
import { inventoryAPI } from './inventory';
export { authAPI, tintometryAPI, inventoryAPI };

// Re-export all API functions for convenience
export const API = {
  auth: authAPI,
  tintometry: tintometryAPI,
  inventory: inventoryAPI,
};

export default API;