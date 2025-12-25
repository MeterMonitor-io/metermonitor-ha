<template>
  <div style="height: calc(100vh - 200px); border-radius: 15px; overflow: scroll;" class="bglight">
    <div v-if="evaluations.length === 0" style="padding: 20px; width: 430px; margin-top: 20%;">
      <n-empty description="Waiting for the first images...">
      </n-empty>
    </div>
    <template v-else>
      <div v-for="[i, evaluation] in evaluations.entries()" :key="i" :class="{outdated: evaluation.outdated}">
        <n-flex :class="{ redbg: evaluation.result == null, econtainer: true }">
          <table>
            <tbody>
              <tr>
                <td>
                  {{ new Date(evaluation.timestamp).toLocaleString() }}
                </td>
                <td colspan="100%" style="text-align: right;" v-if="evaluation.outdated">
                  <b>OUTDATED</b>
                </td>
              </tr>
              <tr>
                <td style="vertical-align: top;">
                  <template v-if="evaluation.total_confidence">
                    <div style="background-color: rgba(255,255,255,0.1); border-radius: 5px; padding: 5px;">
                      Total Confidence:
                      <div :style="{ color: getColor(evaluation.total_confidence), fontSize: '20px' }">
                        <b>{{ (evaluation.total_confidence * 100).toFixed(1) }}</b>%
                      </div>
                    </div>
                  </template>
                  <div v-else :style="{ color: 'red', fontSize: '20px' }">
                    Rejected
                  </div>
                </td>
                <td v-for="(base64, j) in evaluation.th_digits" :key="evaluation.id + '-' + j">
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
                  <span class="confidence small" :style="{ color: getColor(digit[0][1]) }">
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
                  style="text-align: center; border-top: 2px solid rgba(255,255,255,0.6)"
                >
                  <span
                    :class="{
                      adjustment: true,
                      red: digit !== evaluation.predictions[i][0][0],
                      blue: evaluation.predictions[i][0][0] === 'r'
                    }"
                  >

                    <template v-if="i == evaluation.th_digits.length-4">
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
    </template>
  </div>
</template>

<script setup>
import { defineProps, h } from 'vue';
import {NFlex, NTooltip, NEmpty, NButton, NIcon, useDialog} from 'naive-ui';
import { ArchiveOutlined } from '@vicons/material';
import DatasetUploader from "@/components/DatasetUploader.vue";

const dialog = useDialog();

defineProps({
  evaluations: {
    type: Array,
    default: () => []
  },
  name: {
    type: String,
    default: ''
  }
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
      }
    }),
    closable: true,
    style: { width: '600px' }
  });
};
</script>

<style scoped>
.digit {
  margin: 3px;
  height: 40px;
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

.adjustment {
  font-size: 20px;
  margin: 3px;
  color: rgba(255, 255, 255, 0.7);
}

.red {
  color: red;
}

.blue {
  color: dodgerblue;
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

.redbg {
  background-color: rgba(255, 0, 0, 0.1);
}
.bglight {
  background-color: rgba(240, 240, 240, 0.1);
  padding: 10px;
}

.outdated {
  filter: brightness(0.7);
}

</style>
