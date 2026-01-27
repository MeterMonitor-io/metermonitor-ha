<template>
  <n-modal v-model:show="show" preset="card" title="Add source" style="max-width: 860px;" :mask-closable="!saving && !testing">
    <n-space vertical size="large">
      <n-alert type="info" v-if="selectedType === 'mqtt'">
        MQTT sources don’t need manual setup.
        <br />
        When an ESPHome device publishes images to the configured broker/topic, it will appear under “Waiting for setup”.
      </n-alert>

      <n-form :model="form" :disabled="saving || testing" label-placement="top">
        <n-grid :cols="24" :x-gap="12" :y-gap="8">
          <n-form-item-gi :span="24" label="Source type">
            <n-select v-model:value="selectedType" :options="typeOptions" />
          </n-form-item-gi>

          <n-form-item-gi :span="12" label="Watermeter name">
            <n-input v-model:value="form.name" placeholder="e.g. Hauptzaehler" />
          </n-form-item-gi>

          <n-form-item-gi :span="6" label="Enabled">
            <n-switch v-model:value="form.enabled" />
          </n-form-item-gi>

          <n-form-item-gi :span="6" label="Poll interval (s)" v-if="selectedType !== 'mqtt'">
            <n-input-number v-model:value="form.poll_interval_s" :min="1" :max="3600" />
          </n-form-item-gi>

          <!-- Home Assistant camera config -->
          <template v-if="selectedType === 'ha_camera'">
            <n-form-item-gi :span="24" label="Camera entity">
              <n-select
                v-model:value="form.camera_entity_id"
                :options="cameraOptions"
                filterable
                placeholder="Select a Home Assistant camera.* entity"
                :loading="loadingCameras"
              />
            </n-form-item-gi>

            <n-form-item-gi :span="18" label="Flash light entity (optional)">
              <n-space align="center" style="width: 100%;" :wrap="false">
                <n-input
                  v-model:value="form.flash_entity_id"
                  placeholder="e.g. light.watermeter_led"
                />
                <n-button
                  secondary
                  :disabled="!suggestedFlash"
                  @click="useSuggestedFlash"
                >
                  Use suggested
                </n-button>
              </n-space>
              <div style="opacity: 0.7; margin-top: 6px;" v-if="suggestedFlash">
                Suggested: <span class="code-inline">{{ suggestedFlash }}</span>
              </div>
            </n-form-item-gi>

            <n-form-item-gi :span="6" label="Flash delay (ms)">
              <n-input-number v-model:value="form.flash_delay_ms" :min="0" :max="10000" />
            </n-form-item-gi>

            <n-form-item-gi :span="24" label="Test / preview">
              <n-space vertical>
                <n-space>
                  <n-button
                    type="primary"
                    :disabled="!canTest"
                    :loading="testing"
                    @click="testCapture"
                  >
                    Test capture
                  </n-button>

                  <n-button secondary :disabled="!lastCreatedSourceId" @click="openSetupIfExists">
                    Open setup (if created)
                  </n-button>

                  <n-text depth="3" v-if="testHint">
                    {{ testHint }}
                  </n-text>
                </n-space>

                <div v-if="previewBbox" class="preview">
                  <img :src="previewBbox" alt="Preview" />
                </div>
              </n-space>
            </n-form-item-gi>
          </template>

          <!-- HTTP placeholder -->
          <template v-if="selectedType === 'http'">
            <n-form-item-gi :span="24">
              <n-alert type="warning" title="HTTP sources">
                HTTP sources are planned as a third option. For now, you can create the source entry,
                but ingestion endpoints will be wired in the next step.
              </n-alert>
            </n-form-item-gi>
          </template>
        </n-grid>
      </n-form>

      <n-space justify="end">
        <n-button @click="close" :disabled="saving || testing">Cancel</n-button>
        <n-button type="success" @click="create" :loading="saving" :disabled="!canCreate">
          Create source
        </n-button>
      </n-space>
    </n-space>
  </n-modal>
</template>

<script setup>
/* global defineProps, defineEmits */
import { computed, onMounted, ref, watch } from 'vue';
import {
  NModal,
  NSpace,
  NForm,
  NGrid,
  NFormItemGi,
  NSelect,
  NInput,
  NInputNumber,
  NSwitch,
  NButton,
  NAlert,
  NText,
} from 'naive-ui';
import router from '@/router';
import { apiService } from '@/services/api';

const props = defineProps({
  show: { type: Boolean, default: false },
});

const emit = defineEmits(['update:show', 'created']);

const show = computed({
  get: () => props.show,
  set: (v) => emit('update:show', v),
});

const selectedType = ref('ha_camera');

const typeOptions = [
  { label: 'Home Assistant (Camera entity)', value: 'ha_camera' },
  { label: 'MQTT (auto-discovery)', value: 'mqtt' },
  { label: 'HTTP (planned)', value: 'http' },
];

const form = ref({
  name: '',
  enabled: true,
  poll_interval_s: 10,
  camera_entity_id: null,
  flash_entity_id: null,
  flash_delay_ms: 1200,
});

const saving = ref(false);
const testing = ref(false);
const loadingCameras = ref(false);
const cameras = ref([]);
const lastCreatedSourceId = ref(null);
const previewBbox = ref(null);
const testHint = ref('');

const cameraOptions = computed(() =>
  cameras.value.map((c) => ({ label: c.name || c.entity_id, value: c.entity_id, raw: c }))
);

const suggestedFlash = computed(() => {
  const cam = cameras.value.find((c) => c.entity_id === form.value.camera_entity_id);
  return cam?.suggested_flash_entity_id || null;
});

function useSuggestedFlash() {
  if (suggestedFlash.value) {
    form.value.flash_entity_id = suggestedFlash.value;
  }
}

const canCreate = computed(() => {
  if (!form.value.name?.trim()) return false;
  if (selectedType.value === 'mqtt') return true;
  if (!form.value.poll_interval_s || form.value.poll_interval_s < 1) return false;
  if (selectedType.value === 'ha_camera') {
    return !!form.value.camera_entity_id;
  }
  return true;
});

const canTest = computed(() => {
  return selectedType.value === 'ha_camera' && canCreate.value;
});

async function loadCameras() {
  if (selectedType.value !== 'ha_camera') return;
  loadingCameras.value = true;
  try {
    const r = await apiService.getJson('api/ha/cameras');
    cameras.value = r.cameras || [];
  } catch (e) {
    console.error('Failed to load HA cameras', e);
    cameras.value = [];
  } finally {
    loadingCameras.value = false;
  }
}

watch(
  () => selectedType.value,
  async () => {
    previewBbox.value = null;
    testHint.value = '';
    if (selectedType.value === 'ha_camera') await loadCameras();
  }
);

watch(
  () => form.value.camera_entity_id,
  () => {
    // auto-prefill flash if suggested
    const cam = cameras.value.find((c) => c.entity_id === form.value.camera_entity_id);
    if (cam?.suggested_flash_entity_id) {
      form.value.flash_entity_id = cam.suggested_flash_entity_id;
    }
  }
);

function close() {
  show.value = false;
}

async function create() {
  saving.value = true;
  try {
    const payload = {
      name: form.value.name.trim(),
      source_type: selectedType.value,
      enabled: !!form.value.enabled,
      poll_interval_s: selectedType.value === 'mqtt' ? null : form.value.poll_interval_s,
      config: undefined,
    };

    if (selectedType.value === 'ha_camera') {
      payload.config = {
        camera_entity_id: form.value.camera_entity_id,
        flash_entity_id: form.value.flash_entity_id || null,
        flash_delay_ms: form.value.flash_delay_ms,
      };
    }

    await apiService.postJson('api/sources', payload);

    // fetch sources to find id
    const sources = await apiService.getJson('api/sources');
    const created = (sources.sources || []).find(
      (s) => s.name === payload.name && s.source_type === payload.source_type
    );
    lastCreatedSourceId.value = created?.id || null;

    emit('created');
    show.value = false;
  } catch (e) {
    console.error('Create source failed', e);
  } finally {
    saving.value = false;
  }
}

async function testCapture() {
  testing.value = true;
  testHint.value = '';
  previewBbox.value = null;

  try {
    // Ensure source exists
    if (!lastCreatedSourceId.value) {
      await create();
      // modal may be closed by create(); reopen for test
      show.value = true;
    }
    if (!lastCreatedSourceId.value) {
      testHint.value = 'Could not determine source id.';
      return;
    }

    const r = await apiService.postJson(`api/sources/${lastCreatedSourceId.value}/capture-now`, {});

    if (!r.result) {
      testHint.value = r.message || 'Capture failed.';
      return;
    }

    testHint.value = `Capture ok (flash: ${r.flash_used ? 'on' : 'off'})`;

    // Fetch bbox image from meter endpoint (existing endpoint in backend)
    const meter = await apiService.getJson(`api/watermeters/${form.value.name.trim()}`);
    if (meter?.picture?.data_bbox && meter?.picture?.format) {
      previewBbox.value = `data:image/${meter.picture.format};base64,${meter.picture.data_bbox}`;
    } else {
      testHint.value = 'Capture ok, but no bbox preview available yet.';
    }
  } catch (e) {
    console.error('Test capture failed', e);
    testHint.value = 'Test capture failed (see console).';
  } finally {
    testing.value = false;
  }
}

async function openSetupIfExists() {
  if (!form.value.name) return;
  await router.push({ path: `/setup/${form.value.name.trim()}` });
}

onMounted(async () => {
  await loadCameras();
});
</script>

<style scoped>
.code-inline{
  font-family: monospace, monospace;
  padding: 2px 6px;
  border-radius: 6px;
  background-color: rgba(255,255,255,0.08);
}

.preview {
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 10px;
  padding: 10px;
  max-width: 760px;
}
.preview img {
  width: 100%;
  display: block;
  border-radius: 8px;
}
</style>