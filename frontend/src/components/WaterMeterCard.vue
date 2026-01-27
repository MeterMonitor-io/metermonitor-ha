<template>
  <n-card size="small" style="max-width: 300px;">
    <template #header>
      <span class="card-title" :title="meter_name">{{ meter_name }}</span>
    </template>
    <n-flex justify="space-around" size="small" v-if="last_digits" :size="[0,0]" class="theme-revert">
      <img :style="`width:calc(150px / ${last_digits.length});`" class="digit th" v-for="[i,base64] in last_digits.entries()" :key="i + 'c'" :src="'data:image/png;base64,' + base64" :alt="meter_name"/>
    </n-flex>
    <n-flex justify="space-evenly" size="large" v-if="last_result && last_digits">
      <span
          class="prediction google-sans-code"
          v-for="[i, digit] in (last_result + '').padStart(last_digits.length, '0').split('').entries()"
          :key="i + 'd'"
      >
        <template v-if="i === last_digits.length-4">
          {{ (digit[0][0]==='r')? '↕' : digit[0][0] }},
        </template>
        <div v-else-if="i > last_digits.length-4" style="color: #ff9a9a">
          {{ (digit[0][0]==='r')? '↕' : digit[0][0] }}
        </div>
        <template v-else>
          {{ (digit[0][0]==='r')? '↕' : digit[0][0] }}
        </template>

      </span>
    </n-flex>

    <!-- Sparkline Chart -->
    <div v-if="historyData.length > 1" class="sparkline-container">
      <div class="sparkline-labels">
        <span>{{ firstValue }}</span>
        <span>{{ lastValue }}</span>
      </div>
      <apexchart
        type="area"
        height="40"
        width="100%"
        :options="chartOptions"
        :series="chartSeries"
      />
    </div>

    <n-flex justify="space-between">
    </n-flex>
    <template #header-extra>
      {{ last_updated_locale }}
      <n-dropdown :options="menuOptions" @select="handleMenuSelect">
        <n-button text>
          <template #icon>
            <n-icon><MoreVertFilled /></n-icon>
          </template>
        </n-button>
      </n-dropdown>
    </template>
    <template #action>
      <n-flex justify="space-between">
        <router-link v-if="setup" :to="'/setup/'+meter_name"><n-button round>Setup</n-button></router-link>
        <router-link v-else :to="'/meter/'+meter_name"><n-button round>View</n-button></router-link>
        <WifiStatus v-if="rssi" :rssi="rssi" />
      </n-flex>
    </template>
  </n-card>
</template>

<script setup>
import {NCard, NButton, NFlex, NDropdown, NIcon, useDialog} from 'naive-ui';
import {defineProps, computed, ref, onMounted} from 'vue';
import { MoreVertFilled } from '@vicons/material';
import WifiStatus from "@/components/WifiStatus.vue";
import { useThemeStore } from '@/stores/themeStore';
import { storeToRefs } from 'pinia';

const themeStore = useThemeStore();
const { isDark } = storeToRefs(themeStore);

const props = defineProps([
    'meter_name',
    'last_updated', // eg "2025-02-04T03:15:31"
    'setup',
    'last_digits',
    'last_result',
    'rssi'
]);

const historyData = ref([]);
const host = import.meta.env.VITE_HOST;
const dialog = useDialog();

const emit = defineEmits(['removed']);

const menuOptions = [
  { label: 'Remove', key: 'remove' }
];

const handleMenuSelect = (key) => {
  if (key === 'remove') {
    dialog.warning({
      title: 'Confirm Removal',
      content: 'Are you sure you want to remove this meter and its source?',
      positiveText: 'Remove',
      negativeText: 'Cancel',
      onPositiveClick: removeMeter
    });
  }
};

const removeMeter = async () => {
  try {
    const response = await fetch(`${host}api/watermeters/${props.meter_name}`, {
      method: 'DELETE',
      headers: { 'secret': localStorage.getItem('secret') }
    });
    if (response.ok) {
      emit('removed');
    } else {
      console.error('Failed to remove meter');
    }
  } catch (e) {
    console.error('Error removing meter:', e);
  }
};

const loadHistory = async () => {
  if (props.setup) return;
  try {
    const response = await fetch(host + `api/watermeters/${props.meter_name}/history`, {
      headers: { 'secret': localStorage.getItem('secret') }
    });
    if (response.ok) {
      const data = await response.json();
      // Sort by timestamp and take last 20 entries
      historyData.value = (data.history || [])
        .sort((a, b) => new Date(a[1]) - new Date(b[1]))
        .slice(-20);
    }
  } catch (e) {
    console.error('Failed to load history for card:', e);
  }
};

onMounted(() => {
  loadHistory();
});

const last_updated_locale = computed(() => {
  if (!props.last_updated) return '';
  const date = new Date(props.last_updated);
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }) + ' · ' + date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit'
  });
});

const firstValue = computed(() => {
  if (historyData.value.length === 0) return '';
  return (historyData.value[0][0] / 1000).toFixed(1);
});

const lastValue = computed(() => {
  if (historyData.value.length === 0) return '';
  return (historyData.value[historyData.value.length - 1][0] / 1000).toFixed(1);
});

const chartSeries = computed(() => [{
  name: 'Value',
  data: historyData.value.map(item => ({
    x: new Date(item[1]).getTime(),
    y: item[0] / 1000
  }))
}]);

const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    sparkline: { enabled: true },
    animations: { enabled: false },
    background: 'transparent',
  },
  stroke: {
    curve: 'smooth',
    width: 2,
  },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.4,
      opacityTo: 0.1,
    }
  },
  colors: [isDark.value ? '#18bcf2' : '#0891b2'],
  tooltip: {
    enabled: true,
    theme: isDark.value ? 'dark' : 'light',
    x: {
      format: 'dd MMM HH:mm'
    },
    y: {
      formatter: (val) => val.toFixed(2) + ' m³'
    }
  },
  xaxis: {
    type: 'datetime',
  },
  yaxis: {
    show: false,
  },
  grid: {
    show: false,
    padding: { left: 0, right: 0, top: 0, bottom: 0 }
  },
}));
</script>

<style scoped>
.card-title {
  display: block;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.digit{
  mix-blend-mode: screen;
  opacity: 0.4;
}

.prediction{
  width: 16px;
  text-wrap: nowrap;
  font-size: 1.6em;
}

.sparkline-container {
  margin: 8px -16px 0 -16px;
  position: relative;
}

.sparkline-labels {
  display: flex;
  justify-content: space-between;
  padding: 0 8px;
  font-size: 10px;
  opacity: 0.5;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1;
}
</style>