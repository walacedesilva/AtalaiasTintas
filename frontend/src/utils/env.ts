/**
 * Environment configuration utility
 * Provides centralized access to environment variables and configuration
 */

interface Config {
  API_BASE_URL: string;
  APP_NAME: string;
  APP_VERSION: string;
  ENVIRONMENT: 'development' | 'production' | 'test';
  ENABLE_DEVTOOLS: boolean;
  MOCK_API: boolean;
}

function getConfig(): Config {
  const isDev = import.meta.env.DEV;
  const isTest = import.meta.env.MODE === 'test';
  const isProd = import.meta.env.PROD;

  return {
    API_BASE_URL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1',
    APP_NAME: import.meta.env.VITE_APP_NAME || 'Atalaia Tintas',
    APP_VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
    ENVIRONMENT: isTest ? 'test' : isProd ? 'production' : 'development',
    ENABLE_DEVTOOLS: isDev || import.meta.env.VITE_ENABLE_DEVTOOLS === 'true',
    MOCK_API: import.meta.env.VITE_MOCK_API === 'true' || isTest,
  };
}

export const config = getConfig();

// Named exports for convenience
export const {
  API_BASE_URL,
  APP_NAME,
  APP_VERSION,
  ENVIRONMENT,
  ENABLE_DEVTOOLS,
  MOCK_API,
} = config;

// Utility functions
export const isDevelopment = (): boolean => ENVIRONMENT === 'development';
export const isProduction = (): boolean => ENVIRONMENT === 'production';
export const isTest = (): boolean => ENVIRONMENT === 'test';