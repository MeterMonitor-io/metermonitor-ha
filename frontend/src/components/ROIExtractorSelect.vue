<template>
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
    :value="value"
    :options="options"
    :disabled="disabled"
    @update:value="(next) => emit('update:value', next)"
  />
  <div v-if="templateEnabled" class="template-bar">
    <n-button
      size="small"
      :loading="templateSaving"
      :disabled="disabled || templateSaving || !canSaveTemplate"
      @click="emit('save-template')"
    >
      Save template
    </n-button>
    <n-text depth="3" v-if="templateReady">Template saved</n-text>
    <n-text depth="3" v-else>Save template to continue</n-text>
  </div>
</template>

<script setup>
import { NSelect, NTooltip, NIcon, NButton, NText } from 'naive-ui';
import { CropOutlined } from '@vicons/material';

defineProps({
  value: { type: String, required: true },
  options: { type: Array, required: true },
  disabled: { type: Boolean, default: false },
  templateEnabled: { type: Boolean, default: false },
  templateSaving: { type: Boolean, default: false },
  templateReady: { type: Boolean, default: false },
  canSaveTemplate: { type: Boolean, default: false }
});

const emit = defineEmits(['update:value', 'save-template']);
</script>

<style scoped>
.tooltip-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.template-bar {
  margin-top: 8px;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
