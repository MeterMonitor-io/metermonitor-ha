import { useAuthStore } from '@/stores/authStore';

const host = import.meta.env.VITE_HOST;

/**
 * Centralized API service with error handling and auth
 */
class ApiService {
  async request(url, options = {}) {
    const authStore = useAuthStore();
    
    const defaultOptions = {
      headers: {
        'secret': authStore.secret,
        ...options.headers,
      },
    };

    const response = await fetch(host + url, { ...defaultOptions, ...options });
    
    // Check auth status
    authStore.checkAuth(response);
    
    return response;
  }

  async get(url) {
    return this.request(url, { method: 'GET' });
  }

  async post(url, data) {
    const authStore = useAuthStore();
    return this.request(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'secret': authStore.secret,
      },
      body: JSON.stringify(data),
    });
  }

  async getJson(url) {
    const response = await this.get(url);
    if (response.ok) {
      return await response.json();
    }
    throw new Error(`API request failed: ${response.status}`);
  }

  async postJson(url, data) {
    const response = await this.post(url, data);
    if (response.ok) {
      return await response.json();
    }
    throw new Error(`API request failed: ${response.status}`);
  }
}

export const apiService = new ApiService();

