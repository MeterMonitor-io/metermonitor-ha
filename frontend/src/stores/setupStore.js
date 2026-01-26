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
  const runningBenchmark = ref(false);
  const searchingThresholds = ref(false);
  const thresholdSearchResult = ref(null);

  // Actions
  const searchThresholds = async (meterId, steps = 10) => {
    const watermeterStore = useWatermeterStore();

    searchingThresholds.value = true;
    thresholdSearchResult.value = null;

    try {
      const response = await apiService.post(`api/watermeters/${meterId}/search_thresholds`, { steps });

      if (response.ok) {
        const result = await response.json();

        if (result.error) {
          console.error('Threshold search error:', result.error);
          thresholdSearchResult.value = { error: result.error };
          return null;
        }

        thresholdSearchResult.value = result;

        // Apply the found thresholds to settings
        watermeterStore.settings.threshold_low = result.threshold[0];
        watermeterStore.settings.threshold_high = result.threshold[1];
        watermeterStore.settings.threshold_last_low = result.threshold_last[0];
        watermeterStore.settings.threshold_last_high = result.threshold_last[1];

        // Save settings to backend
        await watermeterStore.updateSettings(meterId);

        console.log('Threshold search completed:', result);
        return result;
      } else {
        console.error('Threshold search failed:', response.status);
        thresholdSearchResult.value = { error: `Request failed: ${response.status}` };
        return null;
      }
    } catch (e) {
      console.error('Threshold search exception:', e);
      thresholdSearchResult.value = { error: e.message };
      return null;
    } finally {
      searchingThresholds.value = false;
    }
  };

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
    
    watermeterStore.settings.threshold_low = data.threshold[0];
    watermeterStore.settings.threshold_high = data.threshold[1];
    watermeterStore.settings.threshold_last_low = data.threshold_last[0];
    watermeterStore.settings.threshold_last_high = data.threshold_last[1];
    watermeterStore.settings.islanding_padding = data.islanding_padding;

    // Cancel any ongoing loading and clear random examples
    loadingCancelled.value = true;
    randomExamples.value = [];

    await watermeterStore.updateSettings(meterId);
  };

  const updateMaxFlow = async (value, meterId) => {
    const watermeterStore = useWatermeterStore();
    
    watermeterStore.settings.max_flow_rate = value;
    await watermeterStore.updateSettings(meterId);
  };

  const updateConfThreshold = async (value, meterId) => {
    const watermeterStore = useWatermeterStore();

    watermeterStore.settings.conf_threshold = value;
    await watermeterStore.updateSettings(meterId);
  }

  const updateSegmentationSettings = async (data, meterId) => {
    const watermeterStore = useWatermeterStore();
    
    // Cancel any ongoing loading
    loadingCancelled.value = true;

    watermeterStore.settings.segments = data.segments;
    watermeterStore.settings.extended_last_digit = data.extendedLastDigit;
    watermeterStore.settings.shrink_last_3 = data.last3DigitsNarrow;
    watermeterStore.settings.rotated_180 = data.rotated180;

    await watermeterStore.updateSettings(meterId);
    await reevaluate(meterId);
  };

  const clearEvaluationExamples = (meterId=null) => {
    randomExamples.value = [];
    if (meterId) requestReevaluatedDigits(meterId)
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
      clearEvaluationExamples();
    }
  };

  const requestReevaluatedDigits = async (meterId, amount = 10) => {
    // Clear existing examples and reset cancellation flag
    randomExamples.value = [];
    loadingCancelled.value = false;
    runningBenchmark.value = true;

    try {
      for (let offset = 0; offset < amount; offset++) {
        // Check if loading was cancelled
        if (loadingCancelled.value) {
          console.log('Sample loading cancelled');
          break;
        }

        const url = `api/watermeters/${meterId}/evaluations/sample/-1`;
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
      runningBenchmark.value = false;
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
    console.log('Resetting setup store state');
    currentStep.value = 1;
    randomExamples.value = [];
    noBoundingBox.value = false;
    loading.value = false;
    loadingCancelled.value = false;
    searchingThresholds.value = false;
    thresholdSearchResult.value = null;
  }

  return {
    // State
    currentStep,
    randomExamples,
    noBoundingBox,
    loading,
    runningBenchmark,
    searchingThresholds,
    thresholdSearchResult,
    // Actions
    reset,
    redoDigitEval,
    nextStep,
    setLoading,
    searchThresholds,
    updateThresholds,
    updateMaxFlow,
    updateConfThreshold,
    updateSegmentationSettings,
    clearEvaluationExamples,
    reevaluate,
    requestReevaluatedDigits,
    getData,
  };
});

