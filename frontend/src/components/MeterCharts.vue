<template>
  <div class="bg">
    <apexchart
      v-if="series && series.length > 0"
      width="100%"
      height="300"
      type="area"
      :options="chartOptions"
      :series="series"
    ></apexchart>
    <div v-else style="text-align: center; padding: 20px;">
      No history data available
    </div>
  </div>
  <div class="bg" v-if="confidenceSeries && confidenceSeries.length > 0">
    <apexchart
      width="100%"
      height="200"
      type="line"
      :options="confidenceChartOptions"
      :series="confidenceSeries"
    ></apexchart>
  </div>
</template>

<script setup>
import { computed, defineProps } from 'vue';

const props = defineProps({
  history: {
    type: Object,
    default: null
  }
});

const sortedHistory = computed(() => {
  if (!props.history || !props.history.history) return [];
  return [...props.history.history].sort((a, b) => new Date(a[1]) - new Date(b[1]));
});

const series = computed(() => {
  if (sortedHistory.value.length === 0) return [];

  const data = sortedHistory.value.map(item => {
    // item is [value, timestamp, confidence, manual]
    return {
      x: new Date(item[1]).getTime(),
      y: item[0] / 1000
    };
  });

  return [{
    name: 'Value',
    data: data
  }];
});

const confidenceSeries = computed(() => {
  if (sortedHistory.value.length === 0) return [];

  const data = sortedHistory.value.map(item => {
    // item is [value, timestamp, confidence, manual]
    return {
      x: new Date(item[1]).getTime(),
      y: item[2] * 100
    };
  });

  return [{
    name: 'Confidence',
    data: data
  }];
});

const chartOptions = {
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

const confidenceChartOptions = {
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
</script>

<style scoped>
.bg {
  background-color: rgba(240, 240, 240, 0.1);
  padding: 20px;
  border-radius: 15px;
  margin-bottom: 15px;
}
</style>
