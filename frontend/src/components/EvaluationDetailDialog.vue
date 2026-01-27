<template>
  <n-modal v-model:show="show" preset="card" title="Evaluation Details" style="max-width: 900px;" :mask-closable="true">
    <n-spin :show="loading">
      <div v-if="evaluation" class="eval-detail">
        <!-- Header with timestamp and confidence -->
        <n-space justify="space-between" align="center" style="margin-bottom: 20px;">
          <div>
            <h3 style="margin: 0;">{{ formattedTimestamp(evaluation.timestamp) }}</h3>
            <n-tag v-if="evaluation.outdated" type="warning" size="small" style="margin-top: 4px;">
              OUTDATED
            </n-tag>
          </div>
          <div v-if="evaluation.total_confidence" class="conf-display">
            <div style="font-size: 12px; opacity: 0.7;">Confidence</div>
            <div :style="{ color: getColor(evaluation.used_confidence), fontSize: '24px', fontWeight: 'bold' }">
              <n-tooltip trigger="hover" v-if="evaluation.used_confidence !== -1.0">
                <template #trigger>
                  <span style="cursor: help;">{{ (evaluation.used_confidence * 100).toFixed(1) }}%</span>
                </template>
                Used confidence: Only digits accepted by the correction algorithm
              </n-tooltip>
              <span style="margin: 0 8px; opacity: 0.5;">/</span>
              <n-tooltip trigger="hover">
                <template #trigger>
                  <span :style="{ color: getColor(evaluation.total_confidence), fontSize: '16px', cursor: 'help' }">
                    {{ (evaluation.total_confidence * 100).toFixed(1) }}%
                  </span>
                </template>
                Total confidence: All recognized digits
              </n-tooltip>
            </div>
          </div>
          <div v-else class="rejected-badge">
            REJECTED
          </div>
        </n-space>

        <!-- Digit details -->
        <n-card size="small" title="Digit Analysis" embedded style="margin-bottom: 16px;">
          <n-space vertical>
            <!-- Digit thumbnails -->
            <div>
              <div style="font-size: 12px; opacity: 0.7; margin-bottom: 8px;">Segmented Digits</div>
              <n-flex class="theme-revert">
                <img
                  v-for="(base64, i) in evaluation.th_digits_inverted"
                  :key="'digit-' + i"
                  class="digit-thumb"
                  :src="'data:image/png;base64,' + base64"
                  alt="Digit"
                />
              </n-flex>
            </div>

            <!-- Predictions table -->
            <n-table :bordered="false" :single-line="false" size="small">
              <thead>
                <tr>
                  <th>Position</th>
                  <th>Top Prediction</th>
                  <th>Confidence</th>
                  <th>2nd Choice</th>
                  <th>3rd Choice</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(digit, i) in evaluation.predictions" :key="'pred-' + i">
                  <td><b>{{ i + 1 }}</b></td>
                  <td>
                    <span class="prediction-value">
                      {{ (digit[0][0] === 'r') ? '↕ (rotating)' : digit[0][0] }}
                    </span>
                  </td>
                  <td>
                    <span :style="{ color: getColor(digit[0][1]), fontWeight: 'bold' }">
                      {{ (digit[0][1] * 100).toFixed(1) }}%
                    </span>
                  </td>
                  <td style="opacity: 0.6;">
                    {{ (digit[1][0] === 'r') ? '↕' : digit[1][0] }}: {{ (digit[1][1] * 100).toFixed(1) }}%
                  </td>
                  <td style="opacity: 0.6;">
                    {{ (digit[2][0] === 'r') ? '↕' : digit[2][0] }}: {{ (digit[2][1] * 100).toFixed(1) }}%
                  </td>
                  <td>
                    <n-tag v-if="evaluation.denied_digits && evaluation.denied_digits[i]" type="warning" size="small">
                      Denied
                    </n-tag>
                    <n-tag v-else type="success" size="small">
                      Accepted
                    </n-tag>
                  </td>
                </tr>
              </tbody>
            </n-table>
          </n-space>
        </n-card>

        <!-- Corrected Result -->
        <n-card v-if="evaluation.result" size="small" title="Corrected Result" embedded>
          <n-space align="center" size="large">
            <span
              v-for="(digit, i) in (evaluation.result + '').padStart(evaluation.th_digits.length, '0').split('')"
              :key="'result-' + i"
              :class="{
                'result-digit': true,
                'red': digit !== evaluation.predictions[i][0][0],
                'blue': evaluation.predictions[i][0][0] === 'r',
                'orange': evaluation.denied_digits[i] && evaluation.predictions[i][0][0] != digit
              }"
            >
              <template v-if="i === evaluation.th_digits.length - 4">
                {{ digit }}<span style="opacity: 0.5;">,</span>
              </template>
              <template v-else>
                {{ digit }}
              </template>
            </span>
            <span style="font-size: 24px; opacity: 0.7;">m³</span>
          </n-space>
        </n-card>
      </div>
    </n-spin>
  </n-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import {
  NModal,
  NSpace,
  NCard,
  NGrid,
  NGridItem,
  NEmpty,
  NFlex,
  NTable,
  NTag,
  NSpin,
  NTooltip
} from 'naive-ui';

const props = defineProps({
  show: { type: Boolean, default: false },
  evaluationId: { type: Number, default: null },
  meterName: { type: String, required: true }
});

const emit = defineEmits(['update:show']);

const show = computed({
  get: () => props.show,
  set: (v) => emit('update:show', v)
});

const loading = ref(false);
const evaluation = ref(null);
const host = import.meta.env.VITE_HOST;

const getColor = (value) => {
  value = Math.max(0, Math.min(1, value));
  const hue = value * 120;
  return `hsl(${hue}, 100%, 40%)`;
};

const formattedTimestamp = (ts) => {
  const date = new Date(ts);
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }) + ' · ' + date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

const loadEvaluation = async () => {
  if (!props.evaluationId || !props.meterName) return;

  loading.value = true;
  try {
    const response = await fetch(
      `${host}api/watermeters/${props.meterName}/evals/${props.evaluationId}`,
      {
        headers: { 'secret': localStorage.getItem('secret') }
      }
    );
    if (response.ok) {
      evaluation.value = await response.json();
    }
  } catch (e) {
    console.error('Failed to load evaluation details:', e);
  } finally {
    loading.value = false;
  }
};

watch(() => props.show, (newVal) => {
  if (newVal) {
    loadEvaluation();
  }
});
</script>

<style scoped>
.eval-detail {
  min-height: 200px;
}

.conf-display {
  text-align: right;
  padding: 12px;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.rejected-badge {
  color: #d03050;
  font-size: 24px;
  font-weight: bold;
  padding: 12px;
  background-color: rgba(208, 48, 80, 0.1);
  border-radius: 8px;
}

.digit-thumb {
  height: 50px;
  margin: 4px;
  mix-blend-mode: screen;
  opacity: 0.8;
  border-radius: 4px;
}

.prediction-value {
  font-size: 18px;
  font-weight: bold;
  font-family: 'Google Sans', monospace;
}

.result-digit {
  font-size: 32px;
  font-weight: bold;
  font-family: 'Google Sans', monospace;
  color: rgba(255, 255, 255, 0.9);
}

.light-mode .result-digit {
  color: rgba(0, 0, 0, 0.9);
}

.result-digit.red {
  color: #d03050;
}

.result-digit.blue {
  color: dodgerblue;
}

.result-digit.orange {
  color: orange;
}
</style>
