<template>
  <n-flex>
    <router-link to="/">
      <n-button quaternary round size="large" style="padding: 0; font-size: 16px;">
        ← Back
      </n-button>
    </router-link>
    <img src="@/assets/logo.png" alt="Logo" style="max-width: 100px; margin-left: 20px;" />
    <n-button :loading="loading" @click="loadMeter" round size="large" style="margin-left: 20px;">
      Refresh
    </n-button>
  </n-flex>
  <br />
  <n-flex size="large">
    <div style="max-width: 300px">
      <n-card v-if="data" :title="id" size="small">
        <template #header-extra>
          {{ new Date(data.picture.timestamp).toLocaleString() }}
        </template>
        <template #cover>
          <img
            :src="'data:image/' + data.picture.format + ';base64,' + data.picture.data"
            alt="Watermeter"
            :class="{ rotated: rotated180 }"
          />
        </template>
      </n-card>
      <br>
      <WifiStatus v-if="data" :rssi="data['WiFi-RSSI']" />
      <br><br>
      <n-flex>
        <n-popconfirm @positive-click="resetToSetup">
          <template #trigger>
            <n-button type="info" round style="width: 47%">
              Setup
            </n-button>
          </template>
          While the meter is in setup mode, no values will be published. Are you sure?
        </n-popconfirm>

        <n-popconfirm @positive-click="deleteMeter">
          <template #trigger>
            <n-button type="error" ghost round style="width: 47%">
              Delete
            </n-button>
          </template>
          This will delete the meter with all its settings and data. Are you sure?
        </n-popconfirm>
      </n-flex>
      <br />
      <n-card size="small">
        <n-list>
          <n-list-item>
            <n-thing title="Thresholds" :title-extra="`${threshold[0]} - ${threshold[1]}`" />
          </n-list-item>
          <n-list-item>
            <n-thing title="Last digit thresholds" :title-extra="`${threshold_last[0]} - ${threshold_last[1]}`" />
          </n-list-item>
          <n-list-item>
            <n-thing title="Islanding padding" :title-extra="islanding_padding" />
          </n-list-item>
          <n-list-item>
            <n-thing title="Segments" :title-extra="segments" />
          </n-list-item>
          <n-list-item>
            <n-thing title="Extended last digit" :title-extra="extendedLastDigit ? 'Yes' : 'No'" />
          </n-list-item>
          <n-list-item>
            <n-thing title="Last 3 digits narrow" :title-extra="last3DigitsNarrow ? 'Yes' : 'No'" />
          </n-list-item>
          <n-list-item>
            <n-thing title="Rotated 180" :title-extra="rotated180 ? 'Yes' : 'No'" />
          </n-list-item>
          <n-list-item>
            <n-thing title="Max. flow rate" :title-extra="maxFlowRate + ' m³/h'" />
          </n-list-item>
        </n-list>
      </n-card>
    </div>
    <div style="padding-left: 20px; padding-right: 10px;">
      <EvaluationResultList :decodedEvals="decodedEvals" />
    </div>
    <div style="overflow: hidden;">
      <apex-chart class="bg" width="500" type="line" :series="series" :options="options" />
      <apex-chart class="bg" width="500" type="line" :series="seriesConf" :options="optionsConf" />
    </div>
  </n-flex>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import router from '@/router';
import ApexChart from 'vue3-apexcharts';
import EvaluationResultList from "@/components/EvaluationResultList.vue";
import {NFlex, NCard, NButton, NPopconfirm, NList, NListItem, NThing} from "naive-ui";
import WifiStatus from "@/components/WifiStatus.vue";

const route = useRoute();
const id = route.params.id;

const loading = ref(false);
const data = ref(null);
const evaluations = ref(null);
const history = ref(null);

const threshold = ref([0, 0]);
const threshold_last = ref([0, 0]);
const islanding_padding = ref(0);
const segments = ref(0);
const extendedLastDigit = ref(false);
const last3DigitsNarrow = ref(false);
const rotated180 = ref(false);
const maxFlowRate = ref(1.0);

const decodedEvals = computed(() => {
  return evaluations.value ? evaluations.value.evals.map((encoded) => JSON.parse(encoded)).reverse() : [];
});

const host = import.meta.env.VITE_HOST;

const loadMeter = async () => {
  loading.value = true;
  let response = await fetch(host + 'api/watermeters/' + id, {
    headers: { secret: localStorage.getItem('secret') }
  });
  if (response.status === 401) {
    router.push({ path: '/unlock' });
  }
  data.value = await response.json();

  response = await fetch(host + 'api/watermeters/' + id + '/evals', {
    headers: { secret: localStorage.getItem('secret') }
  });
  evaluations.value = await response.json();

  response = await fetch(host + 'api/watermeters/' + id + '/history', {
    headers: { secret: localStorage.getItem('secret') }
  });
  history.value = await response.json();

  response = await fetch(host + 'api/settings/' + id, {
    headers: { secret: localStorage.getItem('secret') }
  });
  let result = await response.json();
  threshold.value = [result.threshold_low, result.threshold_high];
  threshold_last.value = [result.threshold_last_low, result.threshold_last_high];
  islanding_padding.value = result.islanding_padding;
  segments.value = result.segments;
  extendedLastDigit.value = result.extended_last_digit === 1;
  last3DigitsNarrow.value = result.shrink_last_3 === 1;
  rotated180.value = result.rotated_180 === 1;
  maxFlowRate.value = result.max_flow_rate;

  loading.value = false;
};

onMounted(() => {
  loadMeter();
});

const series = computed(() => {
  if (history.value) {
    return [
      {
        name: 'Consumption m³',
        data: history.value.history.map((item) => [new Date(item[1]), item[0] / 1000])
      }
    ];
  } else {
    return [];
  }
});

const seriesConf = computed(() => {
  if (history.value) {
    return [
      {
        name: 'Confidence in %',
        data: history.value.history.map((item) => [new Date(item[1]), item[2] * 100])
      }
    ];
  } else {
    return [];
  }
});

const options = {
  theme: { mode: 'dark' },
  title: {
    text: 'Consumption',
  },
  chart: {
    type: 'line',
    zoom: { enabled: true },
    background: '#00000000',
  },
  xaxis: {
    type: "datetime",
    labels: {
      rotate: -30, // Less rotation for compactness
      format: "dd MMM HH:mm", // Shorter date format
    },
    tickAmount: 5, // Reduces number of ticks for compactness
  },
  yaxis: {
    title: {text: 'Consumption m³'},
    labels: {
    },
  },
  stroke: { curve: 'smooth' },
  tooltip: {
    x: { format: 'dd MMM HH:mm' },
  }
};

const optionsConf = {
  theme: { mode: 'dark' },
  title: {
    text: 'Confidence',
  },
  chart: {
    type: 'line',
    zoom: { enabled: true },
    background: '#00000000',
  },
  xaxis: {
    type: "datetime",
    labels: {
      rotate: -30, // Less rotation for compactness
      format: "dd MMM HH:mm", // Shorter date format
    },
    tickAmount: 5, // Reduces number of ticks for compactness
  },
  yaxis: {
    title: {text: 'Confidence %'},
    labels: { formatter: (value) => value.toFixed(1) + '%' }
  },
  stroke: { curve: 'smooth' },
  tooltip: {
    x: { format: 'dd MMM HH:mm' },
  }
};

const deleteMeter = async () => {
  let response = await fetch(host + 'api/watermeters/' + id, {
    method: 'DELETE',
    headers: { secret: localStorage.getItem('secret') }
  });
  if (response.status === 200) {
    router.replace({ path: '/' });
  } else {
    console.log('Error deleting meter');
  }
};

const resetToSetup = async () => {
  let response = await fetch(host + 'api/setup/' + id + '/enable', {
    method: 'POST',
    headers: { secret: localStorage.getItem('secret') }
  });
  if (response.status === 200) {
    router.replace({ path: '/setup/' + id });
  } else {
    console.log('Error resetting meter');
  }
};
</script>

<style scoped>
.rotated {
  transform: rotate(180deg);
}
.bg {
  background-color: rgba(240, 240, 240, 0.1);
  padding: 20px;
  border-radius: 15px;
  margin-bottom: 15px;
}
</style>
