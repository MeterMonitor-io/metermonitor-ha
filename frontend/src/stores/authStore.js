import { defineStore } from 'pinia';
import { computed } from 'vue';
import router from '@/router';

export const useAuthStore = defineStore('auth', () => {
  const secret = computed(() => localStorage.getItem('secret'));
  
  const headers = computed(() => ({
    'secret': secret.value,
    'Content-Type': 'application/json',
  }));

  const checkAuth = (response) => {
    if (response.status === 401) {
      router.push({ path: '/unlock' });
      return false;
    }
    return true;
  };

  return {
    secret,
    headers,
    checkAuth,
  };
});

