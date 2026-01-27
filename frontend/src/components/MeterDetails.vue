<template>
  <div style="margin: 0 auto;">
    <n-card v-if="data" :title="id" size="small">
      <template #header-extra>
        {{ formattedTimestamp }}
      </template>
      <template #cover>
        <img
            v-if="data.picture?.data_bbox"
          :src="'data:image/' + data.picture.format + ';base64,' + data.picture.data_bbox"
          alt="Watermeter"
        />
        <img
            v-else
          :src="'data:image/' + data.picture?.format + ';base64,' + data.picture?.data"
          alt="Watermeter"
        />
      </template>
    </n-card>

    <n-alert v-if="!data?.picture?.data_bbox" type="warning" title="No Bounding Box" style="margin-top: 16px;">
      In the last capture, no bounding box was detected. This may indicate that the meter is not properly set up or that the image quality is poor.
    </n-alert>

    <n-alert v-if="store.source?.last_error" type="error" title="Source Error" style="margin-top: 16px;">
      {{ store.source.last_error }}
    </n-alert>

    <br>
    <template v-if="data && data['WiFi-RSSI']">
      <WifiStatus v-if="data && data['WiFi-RSSI']" :rssi="data['WiFi-RSSI']" />
      <br><br>
    </template>
    <n-flex>

      <n-popconfirm @positive-click="emit('triggerCapture')" v-if="store.source?.source_type !== 'mqtt'">
        <template #trigger>
          <n-button type="success" round style="width: 22%" :disabled="store.capturing" :loading="store.capturing">
            Capture
          </n-button>
        </template>
        This will trigger a new picture capture on the source. Are you sure?
      </n-popconfirm>

      <n-popconfirm @positive-click="emit('resetToSetup')">
        <template #trigger>
          <n-button type="info" round style="width: 22%">
            Setup
          </n-button>
        </template>
        While the meter is in setup mode, no values will be published. Are you sure?
      </n-popconfirm>

      <n-popconfirm @positive-click="emit('clearEvaluations')">
        <template #trigger>
          <n-button type="warning" ghost round style="width: 23%">
            Clear Evals
          </n-button>
        </template>
        This will delete all evaluations for this meter. Are you sure?
      </n-popconfirm>

      <n-popconfirm @positive-click="emit('deleteMeter')">
        <template #trigger>
          <n-button type="error" ghost round style="width: 23%">
            Delete
          </n-button>
        </template>
        This will delete the meter with all its settings and data. Are you sure?
      </n-popconfirm>
    </n-flex>
    <template v-if="data && data.dataset_present">
      <br />
      <n-card size="small">
        <n-flex justify="space-between" align="center">
          <b>
            Dataset
          </b>

          <n-button type="primary" ghost round :loading="downloadingDataset" @click="emit('downloadDataset')">
            Download
          </n-button>

          <n-popconfirm @positive-click="emit('deleteDataset')">
            <template #trigger>
              <n-button type="error" ghost circle>
                <template #icon>
                  <n-icon>
                    <DeleteForeverFilled />
                  </n-icon>
                </template>
              </n-button>
            </template>
            This will clear the dataset for this meter. Are you sure?
          </n-popconfirm>
        </n-flex>
      </n-card>
    </template>

    <br />
    <n-thing title="Thresholds" :title-extra="`${settings.threshold_low} - ${settings.threshold_high}`" />
    <n-thing title="Last digit thresholds" :title-extra="`${settings.threshold_last_low} - ${settings.threshold_last_high}`" />
    <n-thing title="Islanding padding" :title-extra="settings.islanding_padding" />
    <n-thing title="Segments" :title-extra="settings.segments" />
    <n-thing title="Extended last digit" :title-extra="settings.extended_last_digit ? 'Yes' : 'No'" />
    <n-thing title="Last 3 digits narrow" :title-extra="settings.shrink_last_3 ? 'Yes' : 'No'" />
    <n-thing title="Rotated 180" :title-extra="settings.rotated_180 ? 'Yes' : 'No'" />
    <n-thing title="Max. flow rate" :title-extra="settings.max_flow_rate + ' m³/h'" />
    <n-thing title="Conf. threshold" :title-extra="settings.conf_threshold + '%'" />
  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue';
import { NCard, NFlex, NButton, NPopconfirm, NList, NListItem, NThing, NIcon, NAlert } from "naive-ui";
import { DeleteForeverFilled } from '@vicons/material';
import WifiStatus from "@/components/WifiStatus.vue";
import {useWatermeterStore} from "@/stores/watermeterStore";

const props = defineProps({
  data: Object,
  settings: Object,
  id: String,
  downloadingDataset: Boolean
});

const store = useWatermeterStore();
const emit = defineEmits(['resetToSetup', 'deleteMeter', 'clearEvaluations', 'downloadDataset', 'deleteDataset', 'triggerCapture']);

const formattedTimestamp = computed(() => {
  if (!props.data?.picture?.timestamp) return '';
  const date = new Date(props.data.picture.timestamp);
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }) + ' · ' + date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit'
  });
});
</script>

<style scoped>
.rotated {
  transform: rotate(180deg);
}
</style>

