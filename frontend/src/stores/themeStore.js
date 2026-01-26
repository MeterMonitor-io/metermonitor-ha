import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';

export const useThemeStore = defineStore('theme', () => {
  // Detect if running in Home Assistant Ingress
  const isHomeAssistant = computed(() => {
    // HA Ingress typically runs in an iframe or has specific URL patterns
    try {
      return window.self !== window.top ||
             window.location.pathname.includes('/hassio_ingress/') ||
             window.location.pathname.includes('/api/hassio_ingress/');
    } catch (e) {
      // Cross-origin iframe access blocked = likely HA
      return true;
    }
  });

  // Theme state: 'dark', 'light', or 'auto'
  const themeMode = ref(localStorage.getItem('themeMode') || 'auto');

  // System/HA preference detection
  const systemPrefersDark = ref(true);

  // Initialize media query listener
  const initSystemThemeDetection = () => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    systemPrefersDark.value = mediaQuery.matches;

    // Listen for system theme changes
    mediaQuery.addEventListener('change', (e) => {
      systemPrefersDark.value = e.matches;
      console.log('[Theme] System theme changed:', e.matches ? 'dark' : 'light');
    });
  };

  // Computed: actual theme to use
  const isDark = computed(() => {
    if (themeMode.value === 'auto') {
      return systemPrefersDark.value;
    }
    return themeMode.value === 'dark';
  });

  // Set theme mode
  const setThemeMode = (mode) => {
    themeMode.value = mode;
    localStorage.setItem('themeMode', mode);
    console.log('[Theme] Theme mode set to:', mode);
  };

  // Watch for theme changes and update body background
  watch(isDark, (dark) => {
    document.body.style.backgroundColor = dark ? '#111111' : '#f5f5f5';
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    document.body.classList.toggle('dark-mode', dark);
    document.body.classList.toggle('light-mode', !dark);
  }, { immediate: true });

  // Initialize on store creation
  initSystemThemeDetection();

  return {
    // State
    themeMode,
    isDark,
    isHomeAssistant,
    systemPrefersDark,

    // Actions
    setThemeMode,
    initSystemThemeDetection,
  };
});
