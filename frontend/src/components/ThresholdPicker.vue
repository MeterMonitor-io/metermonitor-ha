<template>
  <n-card>
    <n-flex>
      <div>
        <n-flex justify="space-around" size="large" v-if="evaluation">
          <img class="digit" v-for="[i,base64] in evaluation['colored_digits'].slice(0,-3).entries()" :src="'data:image/png;base64,' + base64" :key="i+'a'" alt="D" style="height: 50px"/>
        </n-flex>
        <br>
        <n-flex justify="space-around" size="large" v-if="tresholdedImages">
          <img class="digit" v-for="[i,base64] in tresholdedImages.slice(0,-3).entries()" :src="'data:image/png;base64,' + base64" :key="i+'b'" alt="Watermeter" style="height: 50px" />
        </n-flex>
        <br>
        <n-slider :value="threshold" @update:value="updateThreshold" range :step="1" :max="255" @mouseup="sendUpdate" style="max-width: 150px;" :disabled="loading"/>
        {{threshold[0]}} - {{threshold[1]}}
      </div>
      <div>
        <n-flex justify="space-around" size="large" v-if="evaluation">
          <img class="digit" v-for="[i,base64] in evaluation['colored_digits'].slice(-3).entries()" :src="'data:image/png;base64,' + base64" :key="i+'a'" alt="D" style="height: 50px"/>
        </n-flex>
        <br>
        <n-flex justify="space-around" size="large" v-if="tresholdedImages">
          <img class="digit" v-for="[i,base64] in tresholdedImages.slice(-3).entries()" :src="'data:image/png;base64,' + base64" :key="i+'b'" alt="Watermeter" style="height: 50px"/>
        </n-flex>
        <br>
        <n-slider :value="threshold_last" @update:value="updateThresholdLast" range :step="1" :max="255" @mouseup="sendUpdate" style="max-width: 150px;" :disabled="loading"/>
        {{threshold_last[0]}} - {{threshold_last[1]}}
      </div>
    </n-flex>
    <n-divider></n-divider>
    Extraction padding
      <n-slider :value="islanding_padding" @update:value="updateIslandingPadding" :step="1" :max="100" @mouseup="sendUpdate" style="max-width: 150px;" :disabled="loading"/>
    <template #action>
      <n-flex justify="end" size="large">
        <n-button
            @click="() => {emits('reevaluate');emits('next')}"
            round
            :disabled="loading"
        >Apply</n-button>
      </n-flex>
    </template>
  </n-card>
</template>

<script setup>
import {NFlex, NCard, NDivider, NButton, NSlider} from "naive-ui";
import {defineProps, defineEmits, ref, watch, onMounted} from 'vue';

const props = defineProps([
    'evaluation',
    'threshold',
    'threshold_last',
    'islanding_padding',
    'loading'
]);

const emits = defineEmits(['update', 'reevaluate', 'next']);

const currentThreshold = ref(props.threshold);
const currentThresholdLast = ref(props.threshold_last);
const currentIslandingPadding = ref(props.islanding_padding);

const tresholdedImages = ref([]);
const refreshing = ref(false);

const updateThreshold = (value) => {
  currentThreshold.value = value;
};

const updateThresholdLast = (value) => {
  currentThresholdLast.value = value;
};

const updateIslandingPadding = (value) => {
  currentIslandingPadding.value = value;
};

onMounted(() => {
  refreshThresholds();
});

watch(() => props.evaluation, () => {
  refreshThresholds();
});

const sendUpdate = () => {
  emits('update', {
    threshold: currentThreshold.value,
    threshold_last: currentThresholdLast.value,
    islanding_padding: currentIslandingPadding.value,
  });
  refreshThresholds();
}

const refreshThresholds = async () => {
  if (refreshing.value) return;
  if (props.loading) return;
  refreshing.value = true;

  let narray = [];
  const base64s = props.evaluation["colored_digits"];
  for (let j = 0; j < base64s.length; j++) {
    let isLast3 = j >= base64s.length - 3;
    const newBase64 = await thresholdImage(base64s[j], isLast3? currentThresholdLast.value : currentThreshold.value, currentIslandingPadding.value);
    narray.push(newBase64);
  }
  tresholdedImages.value = narray;
  refreshing.value = false;
}

const host = import.meta.env.VITE_HOST;

async function thresholdImage(base64, threshold, islanding_padding = 0) {
  // use endpoint /api/evaluate/single
  const response = await fetch(host + 'api/evaluate/single', {
    method: 'POST',
    headers: {
      'secret': `${localStorage.getItem('secret')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      base64str: base64,
      threshold_low: threshold[0],
      threshold_high: threshold[1],
      islanding_padding: islanding_padding
    })
  });
  const result = await response.json();
  return result.base64;
}

</script>

<style scoped>

</style>