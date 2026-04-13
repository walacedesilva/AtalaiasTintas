import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError
} from 'axios';
import { API_BASE_URL, isDevelopment } from '@/utils/env';
import type { APIError } from '@/types';

/**
 * Main API client for communicating with Django backend
 * Includes authentication, error handling, and request/response interceptors
 */

class APIClient {
  private client: AxiosInstance;
  private authToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    this.setupInterceptors();
    this.loadAuthToken();
  }

  private setupInterceptors(): void {
    // Request interceptor - Add auth token and logging
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        if (this.authToken) {
          config.headers.Authorization = `Token ${this.authToken}`;
        }

        // Add CSRF token if available (for Django compatibility)
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
          config.headers['X-CSRFToken'] = csrfToken;
        }

        // Log request in development
        if (isDevelopment()) {
          console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, {
            data: config.data,
            params: config.params
          });
        }

        return config;
      },
      (error) => {
        if (isDevelopment()) {
          console.error('❌ Request Error:', error);
        }
        return Promise.reject(error);
      }
    );

    // Response interceptor - Error handling and logging
    this.client.interceptors.response.use(
      (response) => {
        if (isDevelopment()) {
          console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
            status: response.status,
            data: response.data
          });
        }
        return response;
      },
      (error: AxiosError) => {
        const apiError = this.handleAPIError(error);
        
        if (isDevelopment()) {
          console.error('❌ API Error:', apiError);
        }

        // Handle auth errors
        if (error.response?.status === 401) {
          this.clearAuthToken();
          // Redirect to login if needed
          window.location.href = '/login';
        }

        return Promise.reject(apiError);
      }
    );
  }

  private handleAPIError(error: AxiosError): APIError {
    const response = error.response;
    
    if (!response) {
      return {
        detail: 'Erro de conexão com o servidor',
        message: 'Verifique sua conexão com a internet',
        status_code: 0
      };
    }

    const data = response.data as any;
    
    return {
      detail: data?.detail || data?.message || 'Erro interno do servidor',
      message: data?.message,
      errors: data?.errors,
      status_code: response.status
    };
  }

  private getCSRFToken(): string | null {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return value ?? null;
      }
    }
    return null;
  }

  // Authentication methods
  setAuthToken(token: string): void {
    this.authToken = token;
    localStorage.setItem('authToken', token);
  }

  clearAuthToken(): void {
    this.authToken = null;
    localStorage.removeItem('authToken');
  }

  private loadAuthToken(): void {
    const token = localStorage.getItem('authToken');
    if (token) {
      this.authToken = token;
    }
  }

  isAuthenticated(): boolean {
    return this.authToken !== null;
  }

  // HTTP methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config);
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
  }

  // Convenience methods for common patterns
  async getData<T>(url: string, params?: Record<string, any>): Promise<T> {
    const response = await this.get<T>(url, { params });
    return response.data;
  }

  async postData<T>(url: string, data: any): Promise<T> {
    const response = await this.post<T>(url, data);
    return response.data;
  }

  async putData<T>(url: string, data: any): Promise<T> {
    const response = await this.put<T>(url, data);
    return response.data;
  }

  async patchData<T>(url: string, data: any): Promise<T> {
    const response = await this.patch<T>(url, data);
    return response.data;
  }

  async deleteData<T>(url: string): Promise<T> {
    const response = await this.delete<T>(url);
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export class for testing purposes
export { APIClient };