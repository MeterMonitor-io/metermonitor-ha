<template>
  <n-flex align="center">
    <n-flex align="center">
      <img src="@/assets/logo.png" alt="Logo" style="max-width: 100px" class="theme-revert"/>
      <n-button :loading="loading" @click="getData" round size="large">Refresh</n-button>
    </n-flex>

    <n-button type="primary" round @click="showAddSource = true">
      Add source
    </n-button>
  </n-flex>

  <AddSourceDialog v-model:show="showAddSource" @created="getData" />

  <template v-if="discoveredMeters.length === 0 && waterMeters.length === 0 && config">
    <n-h2>Welcome to MeterMonitor!</n-h2>
    <n-space vertical size="large">
      <div>
        If you use MQTT, devices will appear automatically once they publish images.<br>
        You can also add a Home Assistant camera source via the button above.
      </div>
      <n-flex>
        <n-button quaternary type="info">
          <a href="https://esphome.io/components/camera/esp32_camera.html" target="_blank" rel="noreferrer" style="text-decoration: none; color: inherit;">
            ESPHome ESP32-CAM setup guide
          </a>
        </n-button>

        <n-button quaternary type="info">
          <a href="https://github.com/phiph-s/metermonitor-managementserver/" target="_blank" rel="noreferrer" style="text-decoration: none; color: inherit;">
            GitHub Documentation
          </a>
        </n-button>
      </n-flex>
      <n-divider />
      <div>
        <b>MQTT payload format</b>
        <div class="code">
          {<br>
          &nbsp;"name": "unique name",<br>
          &nbsp;"picture_number": 57,<br>
          &nbsp;"WiFi-RSSI": -57,<br>
          &nbsp;"picture": {<br>
          &nbsp;&nbsp;"format": "jpeg",<br>
          &nbsp;&nbsp;"timestamp": "2025-...",<br>
          &nbsp;&nbsp;"width": 640,<br>
          &nbsp;&nbsp;"height": 320,<br>
          &nbsp;&nbsp;"length": 12345,<br>
          &nbsp;&nbsp;"data": "..."<br>
          &nbsp;}<br>
          }
        </div>
      </div>

      <div>
        <b>Current MQTT config</b><br />
        Broker: <span class="code-inline">{{ config?.mqtt?.broker }}</span><br />
        Topic: <span class="code-inline">{{ config?.mqtt?.topic }}</span>
      </div>
    </n-space>
  </template>

  <template v-if="discoveredMeters.length > 0">
    <n-h2>Waiting for setup</n-h2>
    <n-flex>
        <WaterMeterCard v-for="item in discoveredMeters" :key="item.id" :last_updated="item[1]" :meter_name="item[0]" :setup="true" :rssi="item[2]"/>
    </n-flex>
  </template>

  <template v-if="waterMeters.length > 0">
    <n-h2>Watermeters</n-h2>
    <n-flex>
        <WaterMeterCard
            v-for="item in waterMeters"
            :key="item.id"
            :last_updated="item[1]"
            :meter_name="item[0]"
            :setup="false"
            :rssi="item[2]"
            :last_digits="item[4]"
            :last_result="item[3]"
        />
    </n-flex>
  </template>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { NH2, NFlex, NButton, NDivider, NCard, NSpace } from 'naive-ui';
import router from "@/router";
import WaterMeterCard from "@/components/WaterMeterCard.vue";
import AddSourceDialog from "@/components/AddSourceDialog.vue";

const discoveredMeters = ref([]);
const waterMeters = ref([]);
const loading = ref(false);
const config = ref(null);
const showAddSource = ref(false);

const host = import.meta.env.VITE_HOST;

// add secret to header of fetch request
const getData = async () => {
  loading.value = true;
  let response = await fetch(host + 'api/discovery', {
    headers: {
      'secret': `${localStorage.getItem('secret')}`
    }
  });
  if (response.status === 401) {
    router.push({ path: '/unlock' });
  }
  discoveredMeters.value = (await response.json())["watermeters"];

  response = await fetch(host + 'api/watermeters', {
    headers: {
      'secret': `${localStorage.getItem('secret')}`
    }
  });
  waterMeters.value = (await response.json())["watermeters"];
  loading.value = false;

  response = await fetch(host + 'api/config', {
    headers: {
      'secret': `${localStorage.getItem('secret')}`
    }
  });
  config.value = await response.json();
}

onMounted(() => {
  getData();
});

</script>

<style scoped>
.code{
  font-family: monospace, monospace;
  background-color: rgba(255,255,255,0.1)
}

div.code{
  background: none;
}

.code-inline{
  font-family: monospace, monospace;
  padding: 2px 6px;
  border-radius: 6px;
  background-color: rgba(255,255,255,0.08);
}
</style>