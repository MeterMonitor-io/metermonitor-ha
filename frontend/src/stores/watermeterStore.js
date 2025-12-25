import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { apiService } from '@/services/api';

export const useWatermeterStore = defineStore('watermeter', () => {
  // State
  const lastPicture = ref(null);
  const evaluation = ref(null);
  const settings = ref({
    threshold_low: 0,
    threshold_high: 100,
    threshold_last_low: 0,
    threshold_last_high: 100,
    islanding_padding: 0,
    segments: 0,
    extended_last_digit: false,
    shrink_last_3: false,
    rotated_180: false,
    max_flow_rate: 1.0,
  });

  // Getters
  const threshold = computed({
    get: () => [settings.value.threshold_low, settings.value.threshold_high],
    set: (value) => {
      settings.value.threshold_low = value[0];
      settings.value.threshold_high = value[1];
    },
  });

  const thresholdLast = computed({
    get: () => [settings.value.threshold_last_low, settings.value.threshold_last_high],
    set: (value) => {
      settings.value.threshold_last_low = value[0];
      settings.value.threshold_last_high = value[1];
    },
  });

  const islandingPadding = computed({
    get: () => settings.value.islanding_padding,
    set: (value) => { settings.value.islanding_padding = value; },
  });

  const segments = computed({
    get: () => settings.value.segments,
    set: (value) => { settings.value.segments = value; },
  });

  const extendedLastDigit = computed({
    get: () => settings.value.extended_last_digit,
    set: (value) => { settings.value.extended_last_digit = value; },
  });

  const last3DigitsNarrow = computed({
    get: () => settings.value.shrink_last_3,
    set: (value) => { settings.value.shrink_last_3 = value; },
  });

  const rotated180 = computed({
    get: () => settings.value.rotated_180,
    set: (value) => { settings.value.rotated_180 = value; },
  });

  const maxFlowRate = computed({
    get: () => settings.value.max_flow_rate,
    set: (value) => { settings.value.max_flow_rate = value; },
  });

  // Actions
  const fetchWatermeter = async (meterId) => {
    const data = await apiService.getJson(`api/watermeters/${meterId}`);
    lastPicture.value = data;
    return data;
  };

  const fetchEvaluations = async (meterId, amount = 1) => {
    const data = await apiService.getJson(`api/watermeters/${meterId}/evals?amount=${amount}`);
    evaluation.value = data.evals && data.evals.length > 0 ? data.evals[0] : null;
    return data;
  };

  const fetchSettings = async (meterId) => {
    const data = await apiService.getJson(`api/settings/${meterId}`);
    
    // Update settings state
    settings.value = {
      threshold_low: data.threshold_low,
      threshold_high: data.threshold_high,
      threshold_last_low: data.threshold_last_low,
      threshold_last_high: data.threshold_last_high,
      islanding_padding: data.islanding_padding,
      segments: data.segments,
      extended_last_digit: data.extended_last_digit === 1,
      shrink_last_3: data.shrink_last_3 === 1,
      rotated_180: data.rotated_180 === 1,
      max_flow_rate: data.max_flow_rate,
    };
    
    return data;
  };

  const updateSettings = async (meterId) => {
    const payload = {
      name: meterId,
      threshold_low: settings.value.threshold_low,
      threshold_high: settings.value.threshold_high,
      threshold_last_low: settings.value.threshold_last_low,
      threshold_last_high: settings.value.threshold_last_high,
      islanding_padding: settings.value.islanding_padding,
      rotated_180: settings.value.rotated_180,
      segments: settings.value.segments,
      extended_last_digit: settings.value.extended_last_digit,
      shrink_last_3: settings.value.shrink_last_3,
      max_flow_rate: settings.value.max_flow_rate,
    };

    await apiService.post('api/settings', payload);
  };

  const fetchAll = async (meterId) => {
    await Promise.all([
      fetchWatermeter(meterId),
      fetchEvaluations(meterId),
      fetchSettings(meterId),
    ]);
  };

  return {
    // State
    lastPicture,
    evaluation,
    settings,
    // Getters
    threshold,
    thresholdLast,
    islandingPadding,
    segments,
    extendedLastDigit,
    last3DigitsNarrow,
    rotated180,
    maxFlowRate,
    // Actions
    fetchWatermeter,
    fetchEvaluations,
    fetchSettings,
    updateSettings,
    fetchAll,
  };
});

