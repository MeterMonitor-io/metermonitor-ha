<template>
  <n-card>
    <template #cover>
      <div class="image-container">
        <img v-if="lastPicture && lastPicture.picture.data_bbox" :src="'data:image/'+lastPicture.picture.format+';base64,' + lastPicture.picture.data_bbox" alt="Watermeter" />
        <img v-else-if="lastPicture" :src="'data:image/'+lastPicture.picture.format+';base64,' + lastPicture.picture.data" alt="Watermeter" />

        <span class="timestamp-overlay">{{ formattedTimestamp }}</span>
        <n-button
          size="tiny"
          type="primary"
          class="recapture-button"
          :loading="capturing"
          :disabled="loading || capturing"
          @click="emits('recapture')"
        >
          <template #icon>
            <n-icon><CameraAltOutlined /></n-icon>
          </template>
          Recapture
        </n-button>
        <div v-if="capturing" class="capture-overlay">
          <n-spin size="small" />
        </div>
      </div>
    </template>
    <br>

    <n-alert v-if="noBoundingBox" title="No bounding box found" type="warning" style="margin-bottom: 15px;">
      Without a bounding box the segmentation will not work. Adjust the camera angle or lighting and try again.
    </n-alert>

    <n-tooltip>
      <template #trigger>
        <span class="tooltip-trigger">
          <n-icon size="16"><CropOutlined /></n-icon>
          <span>ROI Extractor</span>
        </span>
      </template>
      <span>Select the region-of-interest extractor</span>
    </n-tooltip>
    <n-select
      :value="currentExtractor"
      :options="extractorOptions"
      :disabled="loading"
      @update:value="handleUpdate('roiExtractor', $event)"
    />
    <br>
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
    </n-input-number><br>
    <n-flex align="center" :size="8" class="padd">
      <n-switch
        :value="extendedLastDigit"
        @update:value="handleUpdate('extendedLastDigit', $event)"
        :disabled="loading"
      />
      <n-tooltip>
        <template #trigger>
          <span class="tooltip-trigger">
            <n-icon size="16"><AddCircleOutlineOutlined /></n-icon>
            <span>Extended last digit</span>
          </span>
        </template>
        <span>Enable if the last digits display is bigger<br>compared to the other digits</span>
      </n-tooltip>
    </n-flex>
    <n-flex align="center" :size="8" class="padd">
      <n-switch
        :value="last3DigitsNarrow"
        @update:value="handleUpdate('last3DigitsNarrow', $event)"
        :disabled="loading"
      />
      <n-tooltip>
        <template #trigger>
          <span class="tooltip-trigger">
            <n-icon size="16"><CompressOutlined /></n-icon>
            <span>Last 3 digits are narrow</span>
          </span>
        </template>
        <span>Enable if the last three digits displays are narrower<br>compared to the other digits</span>
      </n-tooltip>
    </n-flex>
    <n-flex align="center" :size="8">
      <n-switch
        :value="rotated180"
        @update:value="handleUpdate('rotated180', $event)"
        :disabled="loading"
      />
      <n-tooltip>
        <template #trigger>
          <span class="tooltip-trigger">
            <n-icon size="16"><RotateRightOutlined /></n-icon>
            <span>180° rotated</span>
          </span>
        </template>
        <span>Enable if the captured image is rotated 180°</span>
      </n-tooltip>
    </n-flex>
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
import {NCard, NFlex, NInputNumber, NSwitch, NDivider, NButton, NTooltip, NAlert, NSelect, NSpin, NIcon} from 'naive-ui';
import {defineProps, defineEmits, computed} from 'vue';
import {
  AddCircleOutlineOutlined,
  CameraAltOutlined,
  CompressOutlined,
  CropOutlined,
  RotateRightOutlined
} from '@vicons/material';

const props = defineProps([
    'lastPicture',
    'segments',
    'timestamp',
    'extendedLastDigit',
    'last3DigitsNarrow',
    'evaluation',
    'rotated180',
    'roiExtractor',
    'capturing',
    'loading',
    'noBoundingBox'
]);
const emits = defineEmits(['update', 'next', 'recapture']);

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

const extractorOptions = [
  { label: 'YOLO - Use the YOLOv11 AI-model', value: 'yolo' },
  { label: 'Bypass - Directly segment received images', value: 'bypass' }
];

const currentExtractor = computed(() => props.roiExtractor || 'yolo');

const handleUpdate = (field, value) => {
  emits('update', {
    segments: field === 'segments' ? value : props.segments,
    extendedLastDigit: field === 'extendedLastDigit' ? value : props.extendedLastDigit,
    last3DigitsNarrow: field === 'last3DigitsNarrow' ? value : props.last3DigitsNarrow,
    rotated180: field === 'rotated180' ? value : props.rotated180,
    roiExtractor: field === 'roiExtractor' ? value : props.roiExtractor
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

.recapture-button {
  position: absolute;
  bottom: 8px;
  left: 8px;
  z-index: 2;
}

.capture-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 4px;
}

.digit {
  height: auto;
}

.padd {
  margin-bottom: 10px;
}

.tooltip-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>
