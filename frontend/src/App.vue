<template>

  <n-space vertical size="large">
    <n-layout>
      <n-layout-content content-style="padding: 24px;">
        <router-view></router-view>
      </n-layout-content>
    </n-layout>
  </n-space>

</template>

<script setup>
import {NLayout, NLayoutContent, NSpace, useNotification} from 'naive-ui';
import {onMounted, onUnmounted, ref} from "vue";
import router from "@/router";

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
body{
  background-color: #111111;
}

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

</style>
