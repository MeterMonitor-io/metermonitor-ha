<template>
  <div style="height: calc(100vh - 200px); border-radius: 15px; overflow-y: scroll; overflow-x: hidden;" class="bglight">
    <div v-if="evaluations.length === 0" style="padding: 20px; width: 100%; margin-top: 20%;">
      <n-empty description="Waiting for the first images...">
      </n-empty>
    </div>
    <n-flex v-else justify="center">
      <div v-for="[i, evaluation] in evaluations.entries()" :key="i" :class="{outdated: evaluation.outdated, item: true}">
        <n-flex :class="{ redbg: evaluation.result == null, econtainer: true }">
          <table>
            <tbody>
              <tr class="top-tr">
                <td>
                  {{ formattedTimestamp(evaluation.timestamp) }}
                </td>
                <td colspan="100%" style="text-align: right;" v-if="evaluation.outdated">
                  <b>OUTDATED</b>
                </td>
              </tr>
              <tr>
                <td style="vertical-align: top;">
                  <template v-if="evaluation.total_confidence">
                    <div class="conf_box">
                      Confidence
                      <div :style="{ color: getColor(usedConfidences[i]), fontSize: '20px' }">
                        <n-tooltip trigger="hover">
                          <template #trigger>
                            <span style="cursor: help;"><b>{{ (usedConfidences[i] * 100).toFixed(1) }}</b>%</span>
                          </template>
                          Used confidence: Only digits accepted by the correction algorithm
                        </n-tooltip>
                        <span style="margin: 0 4px;"></span>
                        <n-tooltip trigger="hover">
                          <template #trigger>
                            <span :style="{ color: getColor(evaluation.total_confidence), fontSize: '13px', cursor: 'help' }">{{ (evaluation.total_confidence * 100).toFixed(1) }}%</span>
                          </template>
                          Total confidence: All recognized digits
                        </n-tooltip>
                      </div>
                    </div>
                  </template>
                  <div v-else :style="{ color: 'red', fontSize: '20px' }">
                    Rejected
                  </div>
                </td>
                <td v-for="(base64, j) in evaluation.th_digits_inverted" :key="evaluation.id + '-' + j" class="theme-revert">
                  <img class="digit" :src="'data:image/png;base64,' + base64" alt="Watermeter" />
                </td>
                <td>
                  <n-button
                    size="small"
                    quaternary
                    circle
                    @click="openUploadDialog(evaluation.colored_digits, evaluation.th_digits, name, evaluation.predictions)"
                  >
                    <template #icon>
                      <n-icon><ArchiveOutlined /></n-icon>
                    </template>
                  </n-button>
                </td>
              </tr>
              <tr>
                <td style="opacity: 0.6">
                  Predictions
                </td>
                <td
                  v-for="[i, digit] in evaluation.predictions.entries()"
                  :key="i + 'v'"
                  style="text-align: center;"
                >
                  <n-tooltip>
                    <template #trigger>
                      <span class="prediction small">
                        {{ (digit[0][0] === 'r') ? '↕' : digit[0][0] }}
                      </span>
                    </template>
                    <span>
                      {{ (digit[1][0] === 'r') ? '↕' : digit[1][0] }}: {{ (digit[1][1] * 100).toFixed(1) }}%<br>
                      {{ (digit[2][0] === 'r') ? '↕' : digit[2][0] }}: {{ (digit[2][1] * 100).toFixed(1) }}%
                    </span>
                  </n-tooltip>
                </td>
              </tr>
              <tr>
                <td style="opacity: 0.6">
                  Condifences
                </td>
                <td
                  v-for="[i, digit] in evaluation.predictions.entries()"
                  :key="i + 'e'"
                  style="text-align: center;"
                >
                  <span class="confidence small" :style="{ color: getColor(digit[0][1]), textDecoration: evaluation.denied_digits[i]? 'line-through' : 'none' }">
                    {{ Math.round(digit[0][1] * 100) }}
                  </span>
                </td>
              </tr>
              <tr v-if="evaluation.result">
                <td>
                  Corrected result
                </td>
                <td
                  v-for="[i, digit] in (evaluation.result + '').padStart(evaluation.th_digits.length, '0').split('').entries()"
                  :key="i + 'f'"
                  style="text-align: center; "
                  class="top-border-divider"
                >
                  <span
                    :class="{
                      'google-sans-code': true,
                      adjustment: true,
                      red: digit !== evaluation.predictions[i][0][0],
                      blue: evaluation.predictions[i][0][0] === 'r',
                      orange: evaluation.denied_digits[i] && evaluation.predictions[i][0][0] != digit
                    }"
                  >

                    <template v-if="i === evaluation.th_digits.length-4">
                      {{ digit }},
                    </template>
                    <template v-else>
                      {{ digit }}
                    </template>
                  </span>
                </td>
                <td class="adjustment">m³</td>
              </tr>
            </tbody>
          </table>
        </n-flex>
      </div>
      <div style="display: flex; justify-content: center; margin-top: 10px; width: 100%;">
        <n-button @click="emit('loadMore')">Load more</n-button>
      </div>
    </n-flex>
  </div>
</template>

<script setup>
import {defineProps, h, defineEmits, computed} from 'vue';
import {NFlex, NTooltip, NEmpty, NButton, NIcon, useDialog} from 'naive-ui';
import { ArchiveOutlined } from '@vicons/material';
import DatasetUploader from "@/components/DatasetUploader.vue";

const dialog = useDialog();
const emit = defineEmits(['loadMore', 'datasetUploaded']);

const props = defineProps({
  evaluations: {
    type: Array,
    default: () => []
  },
  name: {
    type: String,
    default: ''
  }
});

// Pre-compute used confidence for all evaluations
const usedConfidences = computed(() => {
  return props.evaluations.map(evaluation => {
    if (!evaluation.predictions || !evaluation.denied_digits) return 1.0;
    let combinedConfidence = 1.0;
    for (let i = 0; i < evaluation.predictions.length; i++) {
      if (!evaluation.denied_digits[i]) {
        combinedConfidence *= evaluation.predictions[i][0][1];
      }
    }
    return combinedConfidence;
  });
});

const getColor = (value) => {
  // Clamp value between 0 and 1 and map it to a hue (red to green)
  value = Math.max(0, Math.min(1, value));
  const hue = value * 120;
  return `hsl(${hue}, 100%, 40%)`;
};

const openUploadDialog = (colored, thresholded, name, values) => {
  const setvalues = values.map(sub => sub[0][0]);
  let dialogInstance;
  dialogInstance = dialog.info({
    title: 'Upload Dataset',
    content: () => h(DatasetUploader , {
      colored,
      thresholded,
      name,
      setvalues,
      onClose: () => {
        dialogInstance?.destroy();
      },
      onUploaded: () => {
        emit('datasetUploaded');
      }
    }),
    closable: true,
    style: { width: '600px' }
  });
};


const formattedTimestamp = (ts) => {
  const date = new Date(ts);
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }) + ' · ' + date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit'
  });
};
</script>

<style scoped>
.digit {
  margin: 3px;
  height: 40px;
  mix-blend-mode: screen;
}

.prediction {
  margin: 3px;
  font-size: 20px;
  cursor: pointer;
}

.prediction.small {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.light-mode .prediction.small {
  color: rgba(0, 0, 0, 0.5);
}

.adjustment {
  font-size: 20px;
  margin: 3px;
  color: rgba(255, 255, 255, 0.7);
}

.light-mode .adjustment {
  color: rgba(0, 0, 0, 0.7);
}

.red {
  color: red;
}

.blue {
  color: dodgerblue;
}

.orange {
  color: orange;
}

.confidence {
  margin: 3px;
  font-size: 12px;
}

.econtainer {
  padding: 10px;
  margin-bottom: 5px;
  border-radius: 10px;
  background-color: rgba(255, 255, 255, 0.05);
}

.light-mode .econtainer {
  background-color: rgba(0, 0, 0, 0.05);
}

.redbg {
  background-color: rgba(255, 0, 0, 0.1);
}

.top-border-divider {
  border-top: 2px solid rgba(255,255,255,0.6);
}

.light-mode .top-border-divider {
  border-top: 2px solid rgba(0,0,0,0.6);
}

.conf_box{
  background-color: rgba(255,255,255,0.1);
  border-radius: 5px;
  padding: 5px;
}

.light-mode .conf_box{
  background-color: rgba(0,0,0,0.05);
}

</style>
