<template>
    <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
        <n-dialog-provider>
          <app></app>
        </n-dialog-provider>
    </n-config-provider>
</template>

<script setup>
import App from "@/App.vue";
import { NConfigProvider, NDialogProvider } from 'naive-ui';
import { darkTheme } from 'naive-ui';

/**
   * Use this for type hints under js file
   * @type import('naive-ui').GlobalThemeOverrides
   */
const themeOverrides = {
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
  }

</script>
<style>

</style>
