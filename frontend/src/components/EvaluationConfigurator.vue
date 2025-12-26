<template>
  <template v-if="evaluation">
    <n-card>
      <n-flex justify="space-around" size="large">
        <img class="digit" v-for="[i,base64] in evaluation['th_digits'].entries()" :key="i + 'c'" :src="'data:image/png;base64,' + base64" alt="D"/>
      </n-flex>
      <n-flex justify="space-around" size="large">
        <span class="prediction google-sans-code" v-for="[i, digit] in evaluation['predictions'].entries()" :key="i + 'd'">
          {{ (digit[0][0]==='r')? '↕' : digit[0][0] }}
        </span>
      </n-flex>
      <n-flex justify="space-around" size="large">
        <span class="confidence google-sans-code" v-for="[i, digit] in evaluation['predictions'].entries()" :key="i + 'e'" :style="{color: getColor(digit[0][1])}">
          {{ (digit[0][1] * 100).toFixed(1) }}
        </span>
      </n-flex><br>
      <n-flex align="center">
        <n-badge
          :value="loading ? '' : `${averageConfidence}%`"
          :processing="loading"
          :type="getBadgeType(averageConfidence)"
          :show="randomExamples && randomExamples.length > 0"
        >
        </n-badge>
        <span style="font-weight: 500;" v-if="randomExamples && randomExamples.length > 0">
          Average Confidence on digits from {{ randomExamples ? randomExamples.length : 0 }} historical evaluations.
        </span>
        <span v-else>
          Press "Apply" to evaluate and run the benchmark.
        </span>
      </n-flex>
      <br>
      <n-collapse v-if="randomExamples && randomExamples.length > 0">
        <n-collapse-item title="Show results" name="1">
          <n-grid :cols="15" y-gap="4">
            <template v-for="[i, example] in randomExamples.entries()" :key="i + 'example'">
              <n-gi justify="space-around" size="small" v-for="[i,base64] in example['processed_images'].entries()" :key="i + 'x'" class="grid-container">
                <img
                    class="digit_small"
                    :src="'data:image/png;base64,' + base64"
                    alt="D"
                />
                <br>
                <span class="prediction_small" :style="{color: getColor(example['predictions'][i][0][1])}">
                  {{ (example['predictions'][i][0][0]==='r')? '↕' : example['predictions'][i][0][0] }}
                </span>
              </n-gi>
            </template>
          </n-grid>
        </n-collapse-item>
      </n-collapse>
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
import {defineProps, ref, defineEmits, computed} from 'vue';
import {NFlex, NCard, NButton, NInputNumber, NDivider, NIcon, NGrid, NGi, NCollapse, NCollapseItem, NBadge, useDialog} from 'naive-ui';
import router from "@/router";

const emit = defineEmits(['update', 'set-loading', 'request-random-example']);

const props = defineProps([
    'meterid',
    'evaluation',
    'timestamp',
    'maxFlowRate',
    'loading',
    'onSetLoading',
    'randomExamples'
]);

const initialValue = ref(0);

const dialog = useDialog();
const host = import.meta.env.VITE_HOST;

// Calculate average confidence from random examples
const averageConfidence = computed(() => {
  if (!props.randomExamples || props.randomExamples.length === 0) {
    return 0;
  }

  let totalConfidence = 0;
  let count = 0;

  props.randomExamples.forEach(example => {
    if (example.predictions) {
      example.predictions.forEach(prediction => {
        if (prediction && prediction[0] && prediction[0][1] !== undefined) {
          totalConfidence += prediction[0][1];
          count++;
        }
      });
    }
  });

  return count > 0 ? ((totalConfidence / count) * 100).toFixed(1) : 0;
});

// Get badge type based on confidence level
const getBadgeType = (confidence) => {
  if (confidence >= 90) return 'success';
  if (confidence >= 75) return 'warning';
  return 'error';
};


const finishSetup = async () => {

  // check if initial value is not 0
  if (initialValue.value === 0) {
    dialog.warning({
      title: 'Initial value',
      content: 'Please enter a valid initial value'
    });
    return;
  }

  // notify parent to show loading
  if (props.onSetLoading) {
    props.onSetLoading(true);
  } else {
    emit('set-loading', true);
  }

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
    if (props.onSetLoading) {
      props.onSetLoading(false);
    } else {
      emit('set-loading', false);
    }
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
  width: 24px;
  height: auto;
}

.digit_small{
  margin: 0px;
  width: 16px;
  height: auto;
}

.prediction{
  margin: 3px;
  font-size: 20px;
}

.prediction_small{
  margin-top: -5px;
  font-size: 20px;
}

.confidence{
  margin: 3px;
  font-size: 10px;
}

.grid-container{
  text-align: center;
  line-height: 0.9;
}
</style>