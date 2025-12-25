<template>
  <template v-if="latestEval">
    <n-card>
      <n-flex justify="space-around" size="large">
        <img class="digit" v-for="[i,base64] in JSON.parse(latestEval)[1].entries()" :key="i + 'c'" :src="'data:image/png;base64,' + base64" alt="D" style="height: 50px"/>
      </n-flex>
      <n-flex justify="space-around" size="large">
        <span class="prediction" v-for="[i, digit] in JSON.parse(latestEval)[2].entries()" :key="i + 'd'">
          {{ (digit[0][0]==='r')? '↕' : digit[0][0] }}
        </span>
      </n-flex>
      <n-flex justify="space-around" size="large">
        <span class="confidence" v-for="[i, digit] in JSON.parse(latestEval)[2].entries()" :key="i + 'e'" :style="{color: getColor(digit[0][1])}">
          {{ (digit[0][1] * 100).toFixed(2) }}
        </span>
      </n-flex>
      <template v-if="randomExamples">
        <template  v-for="[i, example] in randomExamples.entries()" :key="i + 'example'">
          <n-flex justify="space-around" size="large">
            <img class="digit" v-for="[i,base64] in example['processed_images'].entries()" :key="i + 'x'" :src="'data:image/png;base64,' + base64" alt="D" style="height: 50px"/>
          </n-flex>
          <n-flex justify="space-around" size="large">
            <span class="prediction" v-for="[i, digit] in example['predictions'].entries()" :key="i + 'y'">
              {{ (digit[0][0]==='r')? '↕' : digit[0][0] }}
            </span>
          </n-flex>
          <n-flex justify="space-around" size="large">
            <span class="confidence" v-for="[i, digit] in example['predictions'].entries()" :key="i + 'z'" :style="{color: getColor(digit[0][1])}">
              {{ (digit[0][1] * 100).toFixed(2) }}
            </span>
          </n-flex>
        </template>
      </template>
      <n-flex justify="space-around" size="large">
        <n-button quaternary @click="emit('request-random-example', null)" round :disabled="loading">
          <template #icon>
            <n-icon>
              <ShuffleFilled />
            </n-icon>
          </template>
          New random example
        </n-button>
      </n-flex>
      <n-divider />
      <n-flex>
        <div style="max-width: 45%">
          Read initial value
          <n-input-number v-model:value="initialValue" placeholder="Readout" :disabled="loading" />
          <span style="color: rgba(255,255,255,0.3)">{{new Date(timestamp).toLocaleString()}}</span><br>
        </div>
        <div style="max-width: 45%">
          Max. flow rate
          <n-input-number :value="maxFlowRate"
                          @update:value="emit('update', $event)"
                          placeholder="Flow rate" :disabled="loading" />
        </div>
      </n-flex>
      <template #action>
        <n-flex justify="end" size="large">
          <n-button
              @click="finishSetup"
              round
              :disabled="loading"
              :loading="loading"
          >Finish & save</n-button>
        </n-flex>
      </template>
    </n-card>
  </template>
</template>

<script setup>
import {defineProps, ref, defineEmits} from 'vue';
import {NFlex, NCard, NButton, NInputNumber, NDivider, NIcon, useDialog} from 'naive-ui';
import router from "@/router";
import { ShuffleFilled } from '@vicons/material';

const emit = defineEmits(['update', 'set-loading', 'request-random-example']);

const props = defineProps([
    'meterid',
    'latestEval',
    'timestamp',
    'maxFlowRate',
    'loading',
    'onSetLoading',
    'randomExamples'
]);

const initialValue = ref(0);

const dialog = useDialog();
const host = import.meta.env.VITE_HOST;

const finishSetup = async () => {

  // check if initial value is not 0
  if (initialValue.value === 0) {
    dialog.warning({
      title: 'Initial value',
      content: 'Please enter a valid initial value'
    });
    return;
  }

  // notify parent to show global loading
  // prefer direct function prop, then emit, then global event
  try { if (props.onSetLoading) props.onSetLoading(true); } catch (e) {}
  emit('set-loading', true);
  try { window.dispatchEvent(new CustomEvent('global-set-loading', { detail: true })); } catch (e) {}
  try {
    // post to /api/setup/{name}/finish
    const r = await fetch(host + 'api/setup/' + props.meterid + '/finish', {
      method: 'POST',
      headers: {
        'secret': `${localStorage.getItem('secret')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'value': initialValue.value,
        'timestamp': props.timestamp
      })
    });

    if (r.status === 200) {
      router.push({ path: '/meter/' + props.meterid });
    } else {
      console.log('Error finishing setup');
    }
  } catch (e) {
    console.error('finishSetup failed', e);
  } finally {
    // ensure parent loading is turned off if we didn't navigate away
    try { if (props.onSetLoading) props.onSetLoading(false); } catch (e) {}
    emit('set-loading', false);
    try { window.dispatchEvent(new CustomEvent('global-set-loading', { detail: false })); } catch (e) {}
  }

}

function getColor(value) {
  // Clamp the value between 0 and 1
  value = Math.max(0, Math.min(1, value));

  // Map value (0.0 to 1.0) to hue (0 = red, 60 = yellow, 120 = green)
  const hue = value * 120;

  // Using 100% saturation and 40% lightness for good contrast on white.
  return `hsl(${hue}, 100%, 40%)`;
}

</script>

<style scoped>
.digit{
  margin: 3px;
}

.prediction{
  margin: 3px;
  font-size: 20px;
}

.confidence{
  margin: 3px;
  font-size: 10px;
}
</style>