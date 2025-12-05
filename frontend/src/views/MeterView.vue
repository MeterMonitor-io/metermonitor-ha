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
      <template v-if="data.dataset_present">
        <br />
        <n-card size="small">
          <n-flex justify="space-between" align="center">
            <b>
              Dataset
            </b>

            <n-button type="primary" ghost round >
              Download
            </n-button>

            <n-popconfirm @positive-click="deleteMeter">
              <template #trigger>
                <n-button type="error" ghost circle>
                  <template #icon>
                    <n-icon>
                      <DeleteForeverFilled />
                    </n-icon>
                  </template>
                </n-button>
              </template>
              This will clear the dataset for this meter. Are you sure?
            </n-popconfirm>
          </n-flex>
        </n-card>
      </template>
    </div>
    <div style="padding-left: 20px; padding-right: 10px;">
      <EvaluationResultList :decodedEvals="decodedEvals" :name="id"/>
    </div>
    <div style="max-width: 500px;">
      <n-card size="small" style="overflow: hidden;">
        <apex-chart width="468" height="200" type="line" :series="series" :options="options" />
        <apex-chart width="468" height="200" type="line" :series="seriesConf" :options="optionsConf" />
      </n-card>
      <div style="margin-top: 30px; margin-bottom: 15px;">🛈 Correctional Algorithm</div>
      <n-collapse accordion>
        <n-collapse-item title="Per-digit greedy correction" name="1">
          <div>
            Keep flow rate positive: Choose the highest-confidence digit that keeps the reconstructed reading >= last reading prefix.
            Corrected values will be marked in red.<br><br>
            <img src="@/assets/correction.png" alt="Correction example" style="max-width: 100%; border-radius: 15px;"/>
          </div>
        </n-collapse-item>
        <n-collapse-item title="Rotating digits  (↕)" name="2">
          <div>
            When a rotation is detected for a digit, the last accepted value for that digit will be used (marked blue).
            In case a higher order digit increased, the rotating digit will be set to 0.
          </div>
        </n-collapse-item>
        <n-collapse-item title="Negative correction" name="3">
          <div>
            When negative corrections are enabled, the algorithm will accept a slightly lower reading if the previous value looked unreliable but the new prediction is confident.
            After that, it relaxes the acceptance rules for subsequent digits so the full corrected reading can be reconstructed.<br><br>
            <img src="@/assets/negative_correction.png" alt="neg. correction example" style="max-width: 100%; border-radius: 15px;"/>
          </div>
        </n-collapse-item>
        <n-collapse-item title="Rejected results" name="4">
          <div>
            When no valid reading can be reconstructed from the predicted digits or the flow rate exceeds the maximum allowed flow rate,
            the entire evaluation is rejected.
          </div>
        </n-collapse-item>
      </n-collapse>
    </div>
  </n-flex>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import router from '@/router';
import ApexChart from 'vue3-apexcharts';
import EvaluationResultList from "@/components/EvaluationResultList.vue";
import {NFlex, NCard, NButton, NPopconfirm, NList, NListItem, NThing, NCollapse, NCollapseItem, NIcon} from "naive-ui";
import { DeleteForeverFilled } from '@vicons/material';
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
