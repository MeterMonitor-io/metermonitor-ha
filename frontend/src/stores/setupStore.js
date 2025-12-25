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
  const loadingCancelled = ref(false);

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

    // Cancel any ongoing loading and clear random examples
    loadingCancelled.value = true;
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
    
    // Cancel any ongoing loading
    loadingCancelled.value = true;

    watermeterStore.segments = data.segments;
    watermeterStore.extendedLastDigit = data.extendedLastDigit;
    watermeterStore.last3DigitsNarrow = data.last3DigitsNarrow;
    watermeterStore.rotated180 = data.rotated180;

    await watermeterStore.updateSettings(meterId);
    await reevaluate(meterId);
  };

  const clearEvaluationExamples = (meterId = null) => {
    randomExamples.value = [];
    if(meterId) requestReevaluatedDigits(meterId);
  }

  const reevaluate = async (meterId) => {
    // Cancel any ongoing loading
    loadingCancelled.value = true;

    loading.value = true;
    try {
      const response = await apiService.post(`api/watermeters/${meterId}/evaluations/reevaluate`);

      if (response.ok) {
        const result = await response.json();

        if (result.error) {
          console.error('reevaluate error', result.error);
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
      clearEvaluationExamples(meterId);
    }
  };

  const requestReevaluatedDigits = async (meterId, amount = 10) => {
    // Clear existing examples and reset cancellation flag
    randomExamples.value = [];
    loadingCancelled.value = false;
    loading.value = true;

    try {
      // Load samples with increasing offset (0 to amount-1)
      for (let offset = 0; offset < amount; offset++) {
        // Check if loading was cancelled
        if (loadingCancelled.value) {
          console.log('Sample loading cancelled');
          break;
        }

        const url = `api/watermeters/${meterId}/evaluations/sample/${offset}`;
        const response = await apiService.post(url);

        if (response.ok) {
          const result = await response.json();

          if (result.error) {
            console.error('get_reevaluated_digits error', result.error);
            // Stop loading on error
            break;
          }

          // Only add if not cancelled
          if (!loadingCancelled.value) {
            randomExamples.value.push(result);
          }
        } else {
          console.error('Failed to fetch sample at offset', offset);
          // Stop loading if request fails
          break;
        }
      }
    } catch (e) {
      console.error('get_reevaluated_digits failed', e);
    } finally {
      loading.value = false;
    }
  };

  const redoDigitEval = async (meterId) => {
    // Clear existing examples and reset cancellation flag
    loading.value = true;

    const url = `api/watermeters/${meterId}/evaluations/sample`;
    const response = await apiService.post(url);

    if (response.ok) {
      const result = await response.json();

      if (result.error) {
        console.error('redoDigitEval error', result.error);
        loading.value = false;
        return;
      }

      const watermeterStore = useWatermeterStore();
      watermeterStore.evaluation.th_digits = result.processed_images;
      watermeterStore.evaluation.predictions = result.predictions;

      loading.value = false;

    } else {
      console.error('Failed to redo digit evaluation');
      loading.value = false;
    }
  };

  const getData = async (meterId) => {
    loading.value = true;
    const watermeterStore = useWatermeterStore();
    await watermeterStore.fetchAll(meterId);
    loading.value = false;
  };

  const reset = () => {
    currentStep.value = 1;
    randomExamples.value = [];
    noBoundingBox.value = false;
    loading.value = false;
    loadingCancelled.value = false;
  }

  return {
    // State
    currentStep,
    randomExamples,
    noBoundingBox,
    loading,
    // Actions
    reset,
    redoDigitEval,
    nextStep,
    setLoading,
    updateThresholds,
    updateMaxFlow,
    updateSegmentationSettings,
    clearEvaluationExamples,
    reevaluate,
    requestReevaluatedDigits,
    getData,
  };
});

