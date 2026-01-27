<template>
    <n-config-provider :theme="currentTheme" :theme-overrides="currentThemeOverrides">
        <n-dialog-provider>
          <n-message-provider>
            <n-notification-provider :placement="'bottom-right'">
              <app></app>
            </n-notification-provider>
          </n-message-provider>
        </n-dialog-provider>
    </n-config-provider>
</template>

<script setup>
import App from "@/App.vue";
import { NConfigProvider, NDialogProvider, NNotificationProvider, NMessageProvider } from 'naive-ui';
import { darkTheme, lightTheme } from 'naive-ui';
import { computed } from 'vue';
import { useThemeStore } from '@/stores/themeStore';
import { storeToRefs } from 'pinia';

const themeStore = useThemeStore();
const { isDark } = storeToRefs(themeStore);

// Compute current theme based on store
const currentTheme = computed(() => isDark.value ? darkTheme : lightTheme);

// Dark theme overrides
const darkThemeOverrides = {
    common: {
      primaryColor: '#18bcf2',
      bodyColor: '#111111',
    },
    Card: {
      color: '#111111',
      actionColor: '#2c2c2c',
      borderColor: 'rgba(152,152,152,0.68)',
      borderRadius: '10px',
    },
    List: {
      color: '#111111',
      borderColor: 'rgba(152,152,152,0.68)',
      borderRadius: '10px',
    },
    Thing: {
      fontSize: '16px',
    },
    Button: {
      textColorHover: '#18bcf2',
      textColorFocus: '#18bcf2',
      textColorPressed: '#18bcf2',
      borderHover: '#18bcf2',
      borderPressed: '#18bcf2',
      borderFocus: '#18bcf2',
    },
};

// Light theme overrides
const lightThemeOverrides = {
    common: {
      primaryColor: '#0891b2',
      bodyColor: '#f5f5f5',
    },
    Card: {
      color: '#ffffff',
      actionColor: '#f0f0f0',
      borderColor: 'rgba(0,0,0,0.12)',
      borderRadius: '10px',
    },
    List: {
      color: '#ffffff',
      borderColor: 'rgba(0,0,0,0.12)',
      borderRadius: '10px',
    },
    Thing: {
      fontSize: '16px',
    },
    Button: {
      textColorHover: '#0891b2',
      textColorFocus: '#0891b2',
      textColorPressed: '#0891b2',
      borderHover: '#0891b2',
      borderPressed: '#0891b2',
      borderFocus: '#0891b2',
    },
};

// Compute current theme overrides
const currentThemeOverrides = computed(() => isDark.value ? darkThemeOverrides : lightThemeOverrides);

</script>
<style>

</style>
