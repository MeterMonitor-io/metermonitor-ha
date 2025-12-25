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
        <n-slider v-model:value="nthreshold" range :step="1" :max="255" @mouseup="sendUpdate" style="max-width: 150px;" :disabled="loading"/>
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
        <n-slider v-model:value="nthreshold_last" range :step="1" :max="255" @mouseup="sendUpdate" style="max-width: 150px;" :disabled="loading"/>
        {{threshold_last[0]}} - {{threshold_last[1]}}
      </div>
    </n-flex>
    <n-divider></n-divider>
    Extraction padding
      <n-slider v-model:value="islanding_padding" :step="1" :max="100" @mouseup="sendUpdate" style="max-width: 150px;" :disabled="loading"/>
    <template #action>
      <n-flex justify="end" size="large">
        <n-button
            @click="() => {emits('reevaluate');emits('next')}"
            round
            :disabled="loading"
        >(Re)evaluate</n-button>
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

const nthreshold = ref(props.threshold);
const nthreshold_last = ref(props.threshold_last);
const islanding_padding = ref(props.islanding_padding);

const tresholdedImages = ref([]);
const refreshing = ref(false);

onMounted(() => {
  refreshThresholds();
});

watch(() => props.evaluation, () => {
  refreshThresholds();
});
watch(() => props.threshold, (newVal) => {
  nthreshold.value = newVal;
});
watch(() => props.threshold_last, (newVal) => {
  nthreshold_last.value = newVal;
});
watch(() => props.islanding_padding, (newVal) => {
  islanding_padding.value = newVal;
});

const sendUpdate = () => {
  emits('update', {
    threshold: nthreshold.value,
    threshold_last: nthreshold_last.value,
    islanding_padding: islanding_padding.value,
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
    const newBase64 = await thresholdImage(base64s[j], isLast3? nthreshold_last.value : nthreshold.value, islanding_padding.value);
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