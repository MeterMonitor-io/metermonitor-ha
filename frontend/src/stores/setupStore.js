import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiService } from '@/services/api';
import { useWatermeterStore } from './watermeterStore';

export const useSetupStore = defineStore('setup', () => {
  // State
  const currentStep = ref(1);
  const randomExamples = ref([]);
  const noBoundingBox = ref(false);
  const loading = ref(false);

  // Actions
  const nextStep = (step) => {
    if (step === 1) {
      currentStep.value = 2;
    } else if (step === 2) {
      currentStep.value = 3;
    }
  };

  const setLoading = (value) => {
    loading.value = value;
  };

  const updateThresholds = async (data, meterId) => {
    const watermeterStore = useWatermeterStore();
    
    watermeterStore.threshold = data.threshold;
    watermeterStore.thresholdLast = data.threshold_last;
    watermeterStore.islandingPadding = data.islanding_padding;

    // Clear random examples
    randomExamples.value = [];

    await watermeterStore.updateSettings(meterId);
  };

  const updateMaxFlow = async (value, meterId) => {
    const watermeterStore = useWatermeterStore();
    
    watermeterStore.maxFlowRate = value;
    await watermeterStore.updateSettings(meterId);
  };

  const updateSegmentationSettings = async (data, meterId) => {
    const watermeterStore = useWatermeterStore();
    
    watermeterStore.segments = data.segments;
    watermeterStore.extendedLastDigit = data.extendedLastDigit;
    watermeterStore.last3DigitsNarrow = data.last3DigitsNarrow;
    watermeterStore.rotated180 = data.rotated180;

    await watermeterStore.updateSettings(meterId);
    await reevaluate(meterId);
  };

  const reevaluate = async (meterId) => {
    loading.value = true;
    try {
      const response = await apiService.get(`api/reevaluate_latest/${meterId}`);

      if (response.ok) {
        const result = await response.json();

        if (result.error) {
          console.error('get_reevaluated_digits error', result.error);
          return;
        }

        noBoundingBox.value = !result["result"]
      }
    } catch (e) {
      console.error('reevaluate failed', e);
    } finally {
      // Refresh the data
      const watermeterStore = useWatermeterStore();
      await watermeterStore.fetchAll(meterId);
      loading.value = false;
    }
  };

  const requestReevaluatedDigits = async (meterId) => {
    loading.value = true;
    try {
      const response = await apiService.get(`api/get_reevaluated_digits/${meterId}`);
      if (response.ok) {
        const result = await response.json();

        if (result.error) {
          console.error('get_reevaluated_digits error', result.error);
          return;
        }
        randomExamples.value.push(result);

      }
    } catch (e) {
      console.error('get_reevaluated_digits failed', e);
    } finally {
      loading.value = false;
    }
  };

  const getData = async (meterId) => {
    loading.value = true;
    const watermeterStore = useWatermeterStore();
    await watermeterStore.fetchAll(meterId);
    loading.value = false;
  };

  return {
    // State
    currentStep,
    randomExamples,
    noBoundingBox,
    loading,
    // Actions
    nextStep,
    setLoading,
    updateThresholds,
    updateMaxFlow,
    updateSegmentationSettings,
    reevaluate,
    requestReevaluatedDigits,
    getData,
  };
});

