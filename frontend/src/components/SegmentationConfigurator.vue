<template>
  <n-card>
    <template #cover>
      <div class="image-container">
        <img v-if="lastPicture" :src="'data:image/'+lastPicture.picture.format+';base64,' + lastPicture.picture.data_bbox" alt="Watermeter" />
        <span class="timestamp-overlay">{{ formattedTimestamp }}</span>
      </div>
    </template>
    <br>

    <n-alert v-if="noBoundingBox" title="No bounding box found" type="warning" style="margin-bottom: 15px;">
      Without a bounding box the segmentation will not work. Adjust the camera angle or lighting and try again.
    </n-alert>

    <n-tooltip>
      <template #trigger>
        Segments
      </template>
      <span>Number of segments (5-10)</span>
    </n-tooltip>
    <n-input-number
      :value="segments"
      @update:value="handleUpdate('segments', $event)"
      :max="10"
      :min="5"
      :disabled="loading">
    </n-input-number>
    <n-divider dashed></n-divider>
    <n-checkbox
      :checked="extendedLastDigit"
      @update:checked="handleUpdate('extendedLastDigit', $event)"
      :disabled="loading">
      <n-tooltip>
        <template #trigger>
          <span>Extended last digit</span>
        </template>
        <span>Enable if the last digits display is bigger<br>compared to the other digits</span>
      </n-tooltip>
    </n-checkbox><br>
    <n-checkbox
      :checked="last3DigitsNarrow"
      @update:checked="handleUpdate('last3DigitsNarrow', $event)"
      :disabled="loading">
      <n-tooltip>
        <template #trigger>
          <span>Last 3 digits are narrow</span>
        </template>
        <span>Enable if the last three digits displays are narrower<br>compared to the other digits</span>
      </n-tooltip>
    </n-checkbox><br>
    <n-checkbox
      :checked="rotated180"
      @update:checked="handleUpdate('rotated180', $event)"
      :disabled="loading">
      <n-tooltip>
        <template #trigger>
          <span>180° rotated</span>
        </template>
        <span>Enable if the captured image is rotated 180°</span>
      </n-tooltip>
    </n-checkbox><br>
    <template #action v-if="evaluation">
      <n-flex justify="space-around" :size="[0,0]">
        <div v-for="base64 in evaluation['colored_digits']" :key="base64">
          <img :style="`width:calc(350px / ${evaluation['colored_digits'].length});`" class="digit"  :src="'data:image/png;base64,' + base64" alt="D"/>
        </div>
      </n-flex><br>
      <n-flex justify="end">
        <n-button
            @click="emits('next')"
            round
            :disabled="loading"
            :loading="loading"
        >Next</n-button>
      </n-flex>
    </template>
  </n-card>
</template>

<script setup>
import {NCard, NFlex, NInputNumber, NCheckbox, NDivider, NButton, NTooltip, NAlert} from 'naive-ui';
import {defineProps, defineEmits, computed} from 'vue';

const props = defineProps([
    'lastPicture',
    'segments',
    'timestamp',
    'extendedLastDigit',
    'last3DigitsNarrow',
    'evaluation',
    'rotated180',
    'loading',
    'noBoundingBox'
]);
const emits = defineEmits(['update', 'next']);

const formattedTimestamp = computed(() => {
  if (!props.timestamp) return '';
  const date = new Date(props.timestamp);
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }) + ' · ' + date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit'
  });
});

const handleUpdate = (field, value) => {
  emits('update', {
    segments: field === 'segments' ? value : props.segments,
    extendedLastDigit: field === 'extendedLastDigit' ? value : props.extendedLastDigit,
    last3DigitsNarrow: field === 'last3DigitsNarrow' ? value : props.last3DigitsNarrow,
    rotated180: field === 'rotated180' ? value : props.rotated180
  });
};

</script>


<style scoped>
.image-container {
  position: relative;
  display: inline-block;
  width: 100%;
}

.image-container img {
  width: 100%;
  display: block;
}

.timestamp-overlay {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: rgba(255, 255, 255, 0.9);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  backdrop-filter: blur(4px);
}

.digit {
  height: auto;
}
</style>