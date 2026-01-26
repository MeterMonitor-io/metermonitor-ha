<template>
  <n-flex>
    <img src="@/assets/logo.png" alt="Logo" style="max-width: 100px" class="theme-revert"/>
    <n-button :loading="loading" @click="getData" round size="large">Refresh</n-button>
  </n-flex>

  <template v-if="discoveredMeters.length === 0 && waterMeters.length === 0 && config">
    <n-h2>Setup your first monitoring device</n-h2>
    <p>
      No devices were discoverd yet.
      Make sure your device is connected to the mqtt broker on <span class="code">{{config['mqtt']['broker']}}</span>!
    </p>
    <p>
      Currently waiting for messages in the topic <span class="code">{{config['mqtt']['topic']}}</span>. Use the 'refresh' button to check for new devices.
    </p>
    <n-divider/>
    Also make sure your device is publishing the images in the following format:<br><br>
    <div class="code">
      {<br>
          &nbsp;"name": "unique name",<br>
          &nbsp;"picture_number": 57,<br>
          &nbsp;"WiFi-RSSI": -57,<br>
          &nbsp;"picture": {<br>
          &nbsp;&nbsp;	"format": "jpeg",<br>
          &nbsp;&nbsp;	"timestamp": 17...,<br>
          &nbsp;&nbsp;	"width": 640,<br>
          &nbsp;&nbsp;	"height": 320,<br>
          &nbsp;&nbsp;	"length": "...",<br>
          &nbsp;&nbsp;	"data": "..." # Base64-encoded image<br>
          &nbsp;}<br>
      }
    </div>
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
import {onMounted, ref} from 'vue';
import {NH2, NFlex, NButton, NDivider} from 'naive-ui';
import router from "@/router";
import WaterMeterCard from "@/components/WaterMeterCard.vue";

const discoveredMeters = ref([]);
const waterMeters = ref([]);
const loading = ref(false);
const config = ref(null);

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
</style>