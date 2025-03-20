<template>

  <n-flex>
    <router-link to="/"><n-button quaternary round size="large" style="padding: 0; font-size: 16px;">
       ← Back
    </n-button></router-link>
    <img src="@/assets/logo.png" alt="Logo" style="max-width: 100px; margin-left: 20px;"/>
    <n-button :loading="loading" @click="getData" round size="large" style="margin-left: 20px;">Refresh</n-button>
  </n-flex>
    <n-h2>Setup for {{ id }}</n-h2>

  <n-steps :current="currentStep">
    <n-step
      title="Segmentation"
      style="max-width: 500px"
    >
      <div :style="{opacity: (currentStep > 1)?0.5:1.0}">
        <SegmentationConfigurator
            :last-picture="lastPicture"
            :extended-last-digit="extendedLastDigit"
            :last-3-digits-narrow="last3DigitsNarrow"
            :segments="segments"
            :rotated180="rotated180"
            :encoded-latest="evaluations.evals?evaluations.evals[evaluations.evals.length-1]:null"
            @update="updateSegmentationSettings"
            @next="() => nextStep(1)"/>
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
      <div v-if="currentStep > 1" :style="{opacity: (currentStep > 2)?0.5:1.0}">
        <ThresholdPicker
            :encoded="evaluations.evals?evaluations.evals[evaluations.evals.length-1]:null"
            :run="tresholdedImages[tresholdedImages.length-1]"
            :invert="invert"
            :threshold="threshold"
            :threshold_last="threshold_last"
            :islanding_padding="islanding_padding"
            @update="updateThresholds"
            @reevaluate="reevaluate"
            @next="() => nextStep(2)"
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
        <EvaluationViewer :latest-eval="evaluations.evals?evaluations.evals[evaluations.evals.length-1]:null" :meterid="id" :timestamp="lastPicture.picture.timestamp"/>
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
import {onMounted, ref} from 'vue';
import router from "@/router";
import { NSteps, NStep, NButton, NAlert, NFlex, NH2 } from 'naive-ui';
import { useRoute } from 'vue-router';
import SegmentationConfigurator from "@/components/SegmentationConfigurator.vue";
import ThresholdPicker from "@/components/ThresholdPicker.vue";
import EvaluationViewer from "@/components/EvaluationViewer.vue";

const loading = ref(false);

const route = useRoute();
const id = route.params.id;

const lastPicture = ref("");
const evaluations = ref("");

const currentStep = ref(1);
const nextStep = (step) => {
  if (step == 1) {
    currentStep.value = 2;
  } else if (step == 2) {
    currentStep.value = 3;
  }
}

const threshold = ref([0, 100]);
const threshold_last = ref([0, 100]);
const islanding_padding = ref(0);

const tresholdedImages = ref([]);

const segments = ref(0);
const extendedLastDigit = ref(false);
const last3DigitsNarrow = ref(false);
const rotated180 = ref(false);
const invert = ref(false);

const getData = async () => {
  loading.value = true;
  let response = await fetch(process.env.VUE_APP_HOST + 'api/watermeters/' + id, {
    headers: {
      'secret': `${localStorage.getItem('secret')}`
    }
  });
  lastPicture.value = await response.json();

  response = await fetch(process.env.VUE_APP_HOST + 'api/watermeters/' + id + '/evals', {
    headers: {
      'secret': `${localStorage.getItem('secret')}`
    }
  });
  evaluations.value = await response.json();

  response = await fetch(process.env.VUE_APP_HOST + 'api/settings/' + id, {
    headers: {
      'secret': `${localStorage.getItem('secret')}`
    }
  });

  let result = await response.json();

  threshold.value = [result.threshold_low, result.threshold_high];
  threshold_last.value = [result.threshold_last_low, result.threshold_last_high];
  islanding_padding.value = result.islanding_padding;

  segments.value = result.segments;
  extendedLastDigit.value = result.extended_last_digit === 1;
  last3DigitsNarrow.value = result.shrink_last_3 === 1;
  rotated180.value = result.rotated_180 === 1;
  invert.value = result.invert === 1;

  loading.value = false;
}

onMounted(() => {
  // check if secret is in local storage
  const secret = localStorage.getItem('secret');
  if (secret === null) {
    router.push({ path: '/unlock' });
  }
  getData();
});

const updateThresholds = async (data) => {
  threshold.value = data.threshold;
  threshold_last.value = data.threshold_last;
  islanding_padding.value = data.islanding_padding;
  invert.value = data.invert;

  updateSettings();
}

const reevaluate = async () => {
  await fetch(process.env.VUE_APP_HOST + 'api/reevaluate_latest/' + id, {
    method: 'GET',
    headers: {
      'secret': `${localStorage.getItem('secret')}`,
    },
  });
  getData();
}

const updateSegmentationSettings = async (data) => {
  segments.value = data.segments;
  extendedLastDigit.value = data.extendedLastDigit;
  last3DigitsNarrow.value = data.last3DigitsNarrow;
  rotated180.value = data.rotated180;

  await updateSettings();
  reevaluate();
}
const updateSettings = async () => {

  const settings = {
    name: id,
    threshold_low: threshold.value[0],
    threshold_high: threshold.value[1],
    threshold_last_low: threshold_last.value[0],
    threshold_last_high: threshold_last.value[1],
    islanding_padding: islanding_padding.value,
    rotated_180: rotated180.value,
    segments: segments.value,
    extended_last_digit: extendedLastDigit.value,
    shrink_last_3: last3DigitsNarrow.value,
    invert: invert.value
  }

  await fetch(process.env.VUE_APP_HOST + 'api/settings', {
    method: 'POST',
    headers: {
      'secret': `${localStorage.getItem('secret')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(settings)
  });
}



</script>

<style scoped>
</style>