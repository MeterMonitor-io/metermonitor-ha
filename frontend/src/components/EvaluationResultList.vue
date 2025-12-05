<template>
  <div style="height: calc(100vh - 200px); border-radius: 15px; overflow: scroll;" class="bglight">
    <div v-if="decodedEvals.length == 0" style="padding: 20px; width: 430px; margin-top: 20%;">
      <n-empty description="Waiting for the first images...">
      </n-empty>
    </div>
    <template v-if="decodedEvals && decodedEvals.length">
      <template v-for="[i, evalDecoded] in decodedEvals.entries()" :key="i">
        <n-flex :class="{ redbg: evalDecoded[4] == null, econtainer: true }">
          <table>
            <tbody>
              <tr>
                <td>
                  {{ new Date(evalDecoded[3]).toLocaleString() }}
                </td>
              </tr>
              <tr>
                <td style="vertical-align: top;">
                  <template v-if="evalDecoded[6]">
                    <div style="background-color: rgba(255,255,255,0.1); border-radius: 5px; padding: 5px;">
                      Total Confidence:
                      <div :style="{ color: getColor(evalDecoded[6]), fontSize: '20px' }">
                        <b>{{ (evalDecoded[6] * 100).toFixed(1) }}</b>%
                      </div>
                    </div>
                  </template>
                  <div v-else :style="{ color: 'red', fontSize: '20px' }">
                    Rejected
                  </div>
                </td>
                <td v-for="(base64, j) in evalDecoded[1]" :key="evalDecoded[3] + '-' + j">
                  <img class="digit" :src="'data:image/png;base64,' + base64" alt="Watermeter" />
                </td>
                <td>
                  <n-button
                    size="small"
                    quaternary
                    circle
                    @click="openUploadDialog(evalDecoded[0], evalDecoded[1], name)"
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
                  v-for="[i, digit] in evalDecoded[2].entries()"
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
                  v-for="[i, digit] in evalDecoded[2].entries()"
                  :key="i + 'e'"
                  style="text-align: center;"
                >
                  <span class="confidence small" :style="{ color: getColor(digit[0][1]) }">
                    {{ Math.round(digit[0][1] * 100) }}
                  </span>
                </td>
              </tr>
              <tr v-if="evalDecoded[5] && !evalDecoded[5].every(num => num === null)">
                <td style="opacity: 0.6">
                  Add. Prediction
                </td>
                <td
                  v-for="[i, digit] in evalDecoded[5].entries()"
                  :key="i + 'g'"
                  style="text-align: center;"
                >
                  <span class="prediction small" v-if="digit !== evalDecoded[2][i][0][0]">
                    {{ digit ? digit[0] : '' }}
                  </span>
                </td>
              </tr>
              <tr v-if="evalDecoded[5] && !evalDecoded[5].every(num => num === null)">
                <td style="opacity: 0.6">
                  Add. Conf.
                </td>
                <td
                  v-for="[i, digit] in evalDecoded[5].entries()"
                  :key="i + 'h'"
                  style="text-align: center;"
                >
                  <span class="confidence small" :style="{ color: getColor(digit ? digit[1] : 0) }">
                    {{ digit ? digit[1] : '' }}
                  </span>
                </td>
              </tr>
              <tr v-if="evalDecoded[4]">
                <td>
                  Corrected result
                </td>
                <td
                  v-for="[i, digit] in (evalDecoded[4] + '').padStart(evalDecoded[1].length, '0').split('').entries()"
                  :key="i + 'f'"
                  style="text-align: center; border-top: 2px solid rgba(255,255,255,0.6)"
                >
                  <span
                    :class="{
                      adjustment: true,
                      red: digit !== evalDecoded[2][i][0][0],
                      blue: evalDecoded[2][i][0][0] === 'r'
                    }"
                  >

                    <template v-if="i == evalDecoded[2].length-4">
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
      </template>
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
  decodedEvals: {
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

const openUploadDialog = (colored, thresholded, name) => {
  dialog.info({
    title: 'Upload Dataset',
    content: () => h(DatasetUploader , { colored, thresholded, name }),
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
.bglight
{
  background-color: rgba(240, 240, 240, 0.1);
  padding: 10px;
}

</style>
