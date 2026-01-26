<template>

  <n-space vertical size="large">
    <n-layout>
      <n-layout-content content-style="padding: 24px;">
        <!-- Theme toggle in top-right corner -->
        <div style="position: fixed; top: 12px; right: 12px; z-index: 1000;">
          <n-tooltip trigger="hover">
            <template #trigger>
              <n-button
                circle
                quaternary
                size="small"
                @click="cycleTheme"
              >
                <template #icon>
                  <n-icon size="18">
                    <LightModeOutlined v-if="!isDark" />
                    <DarkModeOutlined v-else />
                  </n-icon>
                </template>
              </n-button>
            </template>
            {{ themeTooltip }}
          </n-tooltip>
        </div>
        <router-view></router-view>
      </n-layout-content>
    </n-layout>
  </n-space>

</template>

<script setup>
import {NLayout, NLayoutContent, NSpace, NButton, NIcon, NTooltip, useNotification} from 'naive-ui';
import { LightModeOutlined, DarkModeOutlined } from '@vicons/material';
import {onMounted, onUnmounted, ref, computed} from "vue";
import router from "@/router";
import { useThemeStore } from '@/stores/themeStore';
import { storeToRefs } from 'pinia';

const themeStore = useThemeStore();
const { isDark, themeMode, isHomeAssistant } = storeToRefs(themeStore);

const themeTooltip = computed(() => {
  if (themeMode.value === 'auto') {
    return isHomeAssistant.value
      ? 'Auto (synced with Home Assistant)'
      : 'Auto (follows system)';
  }
  return themeMode.value === 'dark' ? 'Dark mode' : 'Light mode';
});

const cycleTheme = () => {
  // Cycle: auto -> light -> dark -> auto
  const modes = ['auto', 'light', 'dark'];
  const currentIndex = modes.indexOf(themeMode.value);
  const nextIndex = (currentIndex + 1) % modes.length;
  themeStore.setThemeMode(modes[nextIndex]);
};

const alerts = ref([]);

const notification = useNotification();
const host = import.meta.env.VITE_HOST;

const updateAlerts = async () => {
  const r = await fetch(host + 'api/alerts', {
    headers: {secret: localStorage.getItem('secret')}
  })

  if (r.status === 401) {
    await router.push({path: '/unlock'});
    return;
  }

  alerts.value = await r.json();
  notification.destroyAll();
  for (const alert of Object.keys(alerts.value)) {
    notification.create({
      title: alert.toUpperCase(),
      content: alerts.value[alert],
      closable: false,
      type: 'error'
    });
  }
}
const interval = ref(null);
onMounted(() => {
  updateAlerts();
  interval.value = setInterval(updateAlerts, 60000);
});

onUnmounted(() => {
  clearInterval(interval.value);
});

</script>
<style>

.apexcharts-tooltip {
  background: #f3f3f3;
  color: #292929;
}

.google-sans-code {
  font-family: "Google Sans Code", monospace;
  font-optical-sizing: auto;
  font-weight: 600;
  font-style: normal;
}

.light-mode .theme-revert {
  mix-blend-mode: multiply;
  filter: invert(1);
}
</style>
