<template>
  <n-card>
    <template #cover>
      <img v-if="lastPicture" :src="'data:image/'+lastPicture.picture.format+';base64,' + lastPicture.picture.data" alt="Watermeter" :class="{rotated: nrotated180}" />
    </template>
    <br>

    <n-alert v-if="noBoundingBox" title="No bounding box found" type="warning" style="margin-bottom: 15px;">
      Without a bounding box the segmentation will not work. Adjust the camera angle or lighting and try again.
    </n-alert>

    <n-tooltip>
      <template #trigger>
        Segments
      </template>
      <span>Number of segments (5-10)</span>
    </n-tooltip>
    <n-input-number v-model:value="nsegments" :max="10" :min="5" :disabled="loading">
    </n-input-number>
    <n-divider dashed></n-divider>
    <n-checkbox v-model:checked="nextendedLastDigit" :disabled="loading">
      <n-tooltip>
        <template #trigger>
          <span>Extended last digit</span>
        </template>
        <span>Enable if the last digits display is bigger<br>compared to the other digits</span>
      </n-tooltip>
    </n-checkbox><br>
    <n-checkbox v-model:checked="nlast3DigitsNarrow" :disabled="loading">
      <n-tooltip>
        <template #trigger>
          <span>Last 3 digits are narrow</span>
        </template>
        <span>Enable if the last three digits displays are narrower<br>compared to the other digits</span>
      </n-tooltip>
    </n-checkbox><br>
    <n-checkbox v-model:checked="nrotated180" :disabled="loading">
      <n-tooltip>
        <template #trigger>
          <span>180° rotated</span>
        </template>
        <span>Enable if the captured image is rotated 180°</span>
      </n-tooltip>
    </n-checkbox><br>
    <template #action v-if="nEvaluation">
      <n-flex justify="space-around" size="large">
        <img class="digit" v-for="base64 in nEvaluation['colored_digits']" :src="'data:image/png;base64,' + base64" :key="base64" alt="D" style="max-width: 40px"/>
      </n-flex><br>
      <n-flex justify="end" size="large">
        <n-button
            @click="emits('next')"
            round
            :disabled="loading"
            :loading="loading"
        >Next</n-button>
      </n-flex>
    </template>
  </n-card>
</template>

<script setup>
import {NCard, NFlex, NInputNumber, NCheckbox, NDivider, NButton, NTooltip, NAlert} from 'naive-ui';
import {defineProps, defineEmits, ref, watch} from 'vue';

const props = defineProps([
    'lastPicture',
    'segments',
    'extendedLastDigit',
    'last3DigitsNarrow',
    'evaluation',
    'rotated180',
    'loading',
    'noBoundingBox'
]);
const emits = defineEmits(['update', 'next']);

watch(() => props.segments, (newVal) => {
  nsegments.value = newVal;
});
watch(() => props.extendedLastDigit, (newVal) => {
  nextendedLastDigit.value = newVal;
});
watch(() => props.last3DigitsNarrow, (newVal) => {
  nlast3DigitsNarrow.value = newVal;
});
watch(() => props.evaluation, (newVal) => {
  nEvaluation.value = newVal;
});
watch(() => props.rotated180, (newVal) => {
  nrotated180.value = newVal;
});

const nsegments = ref(props.segments);
const nextendedLastDigit = ref(props.extendedLastDigit);
const nlast3DigitsNarrow = ref(props.last3DigitsNarrow);
const nEvaluation = ref(props.evaluation);
const nrotated180 = ref(props.rotated180);

watch([nsegments, nextendedLastDigit, nlast3DigitsNarrow, nrotated180], () => {
  emits('update', {
    segments: nsegments.value,
    extendedLastDigit: nextendedLastDigit.value,
    last3DigitsNarrow: nlast3DigitsNarrow.value,
    rotated180: nrotated180.value
  });
});


</script>


<style scoped>
.rotated{
  transform: rotate(180deg);
}
</style>