<template>

  <n-flex>
    <router-link to="/"><n-button quaternary round size="large" style="padding: 0; font-size: 16px;">
       ← Back
    </n-button></router-link>
    <img src="@/assets/logo.png" alt="Logo" style="max-width: 100px; margin-left: 20px;"/>
    <n-button :loading="loading" @click="setupStore.getData" round size="large" style="margin-left: 20px;">Refresh</n-button>
  </n-flex>
    <n-h2>Setup for {{ id }}</n-h2>

  <n-steps :current="currentStep">
    <n-step
      title="Segmentation"
      style="max-width: 500px"
    >
      <div :style="{opacity: (currentStep > 1)?0.7:1.0}">
        <SegmentationConfigurator
            :last-picture="lastPicture"
            :extended-last-digit="extendedLastDigit"
            :last-3-digits-narrow="last3DigitsNarrow"
            :segments="segments"
            :rotated180="rotated180"
            :evaluation="evaluation"
            :loading="loading"
            :no-bounding-box="noBoundingBox"
            @update="(settings) => setupStore.updateSegmentationSettings(settings, id)"
            @next="() => setupStore.nextStep(1)"/>
        <br>
        <n-alert title="Example" type="info">
          <img src="@/assets/example_segmentation.png" alt="Example segmentation" style="max-width: 100%"/>
            <li>Numbers should be entirely visible</li>
            <li>One number per segement</li>
        </n-alert>
      </div>
    </n-step>
    <n-step
      title="Threshold Extraction"
      style="max-width: 600px"
    >
      <div v-if="currentStep > 1" :style="{opacity: (currentStep > 2)?0.7:1.0}">
        <ThresholdPicker
            :evaluation="evaluation"
            :run="tresholdedImages[tresholdedImages.length-1]"
            :threshold="threshold"
            :threshold_last="thresholdLast"
            :islanding_padding="islandingPadding"
            :loading="loading"
            @update="(data) => setupStore.updateThresholds(data, id)"
            @reevaluate="() => setupStore.reevaluate(id)"
            @next="() => setupStore.nextStep(2)"
        />
        <br>
        <n-alert title="Example" type="info">
          <img src="@/assets/example_thresholds.png" alt="Example segmentation" style="max-width: 100%"/>
          <li>Select thresholds to extract numbers</li>
          <li>Numbers should be clearly visible</li>
          <li>Use the "evaluate" button to test the values</li>
          <li>Use "extraction padding" to remove as much artifacts as possible</li>
        </n-alert>
      </div>
    </n-step>
    <n-step
      title="Evaluation Preview"
      v-if="lastPicture"
      style="max-width: 620px"
    >
      <div v-if="currentStep > 2">
        <EvaluationConfigurator
            :evaluation="evaluation"
            :max-flow-rate="maxFlowRate" :loading="loading"
            @update="(data) => setupStore.updateMaxFlow(data, id)"
            @set-loading="setupStore.setLoading"
            @request-random-example="() => setupStore.requestReevaluatedDigits(id)"
            :meterid="id"
            :timestamp="lastPicture.picture.timestamp"
            :randomExamples="randomExamples"
        />
         <br>
        <n-alert title="Info" type="info">
          <li>Check the values the model extracted</li>
          <li>Reflections and uneven lighting can cause issues</li>
          <li>Manually enter the correct value without a decimal point or leading zeros</li>
        </n-alert>
      </div>
    </n-step>
  </n-steps>

</template>

<script setup>
import { onMounted, computed } from 'vue';
import { NSteps, NStep, NButton, NAlert, NFlex, NH2 } from 'naive-ui';
import { useRoute } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useWatermeterStore } from '@/stores/watermeterStore';
import { useSetupStore } from '@/stores/setupStore';
import SegmentationConfigurator from "@/components/SegmentationConfigurator.vue";
import ThresholdPicker from "@/components/ThresholdPicker.vue";
import EvaluationConfigurator from "@/components/EvaluationConfigurator.vue";

const route = useRoute();
const id = route.params.id;

// Initialize stores
const watermeterStore = useWatermeterStore();
const setupStore = useSetupStore();

// Get reactive state from stores
const { lastPicture, evaluation, threshold, thresholdLast, islandingPadding,
        segments, extendedLastDigit, last3DigitsNarrow, rotated180, maxFlowRate } = storeToRefs(watermeterStore);
const { currentStep, randomExamples, noBoundingBox, loading } = storeToRefs(setupStore);

// Computed property for tresholdedImages (keeping backwards compatibility)
const tresholdedImages = computed(() => {
  return evaluation.value?.tresholded_images || [];
});

onMounted(() => {
  setupStore.getData(id);
});
</script>

<style scoped>
</style>