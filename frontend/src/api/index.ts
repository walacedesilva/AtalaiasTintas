/**
 * API module index
 * Centralized exports for all API modules
 */

export { apiClient, APIClient } from './client';

import { authAPI } from './auth';
import { tintometryAPI } from './tintometry';
import { inventoryAPI } from './inventory';
import { salesAPI } from './sales';
import { fiscalAPI } from './fiscal';
import { monitoringAPI } from './monitoring';

export { 
  authAPI, 
  tintometryAPI, 
  inventoryAPI, 
  salesAPI, 
  fiscalAPI, 
  monitoringAPI 
};

// Re-export all API functions for convenience
export const API = {
  auth: authAPI,
  tintometry: tintometryAPI,
  inventory: inventoryAPI,
  sales: salesAPI,
  fiscal: fiscalAPI,
  monitoring: monitoringAPI,
};

export default API;