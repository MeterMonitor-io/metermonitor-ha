<template>
  <n-card
    size="small"
    class="source-collapse"
    :style="{ '--source-color': sourceColor }"
  >
    <div class="source-header" @click="toggleExpanded">
      <div class="source-left">
        <n-icon :size="20" :color="sourceColor">
          <component :is="sourceIcon" />
        </n-icon>
        <div class="source-title">
          <div class="source-name">{{ sourceTitle }}</div>
        </div>
      </div>
      <div class="source-actions">
        <n-tag size="small" :type="sourceEnabled ? 'success' : 'default'">
          {{ sourceEnabled ? 'Enabled' : 'Disabled' }}
        </n-tag>
        <n-button
          text
          :disabled="!canEdit"
          @click.stop="toggleEditing"
        >
          <n-icon>
            <EditOutlined />
          </n-icon>
        </n-button>
        <n-icon class="chevron" :class="{ open: expanded }">
          <ExpandMoreOutlined />
        </n-icon>
      </div>
    </div>

    <n-collapse-transition>
      <div v-show="expanded" class="source-body">
        <template v-if="editing">
          <n-form :model="form" label-placement="top">
            <n-grid cols="24" x-gap="12" y-gap="8">
              <n-form-item-gi :span="12" label="Enabled">
                <n-switch v-model:value="form.enabled" />
              </n-form-item-gi>
              <n-form-item-gi v-if="showPollInterval" :span="12" label="Poll interval (m)">
                <n-input-number v-model:value="form.poll_interval_m" :min="1" :max="3600" />
              </n-form-item-gi>

              <template v-if="isHaSource">
                <n-form-item-gi :span="24" label="Camera entity">
                  <n-select
                    v-model:value="form.camera_entity_id"
                    :options="cameraOptions"
                    filterable
                    placeholder="Select camera"
                    :loading="loadingCameras"
                  />
                </n-form-item-gi>
                <n-form-item-gi :span="12" label="Flash light entity">
                  <n-space vertical style="width: 100%;">
                    <n-space align="center" style="width: 100%;" :wrap="false">
                      <n-input
                        v-model:value="form.flash_entity_id"
                        :disabled="!form.flash_enabled"
                      />
                      <n-button
                        circle
                        secondary
                        :disabled="!suggestedFlash || !form.flash_enabled"
                        @click="useSuggestedFlash"
                      >
                        <template #icon>
                          <n-icon>
                            <AutoFixHighOutlined />
                          </n-icon>
                        </template>
                      </n-button>
                    </n-space>
                    <n-text depth="3" v-if="suggestedFlash && form.flash_enabled">
                      Suggested: <span class="code-inline">{{ suggestedFlash }}</span>
                    </n-text>
                  </n-space>
                </n-form-item-gi>
                <n-form-item-gi :span="6" label="Flash enabled">
                  <n-switch v-model:value="form.flash_enabled" />
                </n-form-item-gi>
                <n-form-item-gi :span="6" label="Flash delay (ms)">
                  <n-input-number
                    v-model:value="form.flash_delay_ms"
                    :min="0"
                    :max="10000"
                    :disabled="!form.flash_enabled"
                  />
                </n-form-item-gi>
              </template>

              <template v-if="isHttpSource">
                <n-form-item-gi :span="24" label="Image URL">
                  <n-input v-model:value="form.http_url" placeholder="https://example.com/camera.jpg" />
                </n-form-item-gi>
                <n-form-item-gi :span="12" label="Headers (JSON)">
                  <n-input
                    v-model:value="form.http_headers"
                    type="textarea"
                    :autosize="{ minRows: 3, maxRows: 6 }"
                    placeholder='{"Authorization": "Bearer ..."}'
                  />
                </n-form-item-gi>
                <n-form-item-gi :span="12" label="Body (optional)">
                  <n-input
                    v-model:value="form.http_body"
                    type="textarea"
                    :autosize="{ minRows: 3, maxRows: 6 }"
                    placeholder="Optional body (sent with GET)"
                  />
                </n-form-item-gi>
              </template>
            </n-grid>

            <n-space justify="end" style="margin-top: 8px;">
              <n-button @click="cancelEditing">Cancel</n-button>
              <n-button type="primary" :loading="saving" @click="saveChanges">Save</n-button>
            </n-space>
          </n-form>
        </template>

        <template v-else>
          <n-grid cols="2 s:1 m:2 l:2" x-gap="12" y-gap="8">
            <n-grid-item>
              <div class="meta-label">Type</div>
              <div class="meta-value">{{ sourceTitle }}</div>
            </n-grid-item>
            <n-grid-item>
              <div class="meta-label">Name</div>
              <div class="meta-value">{{ sourceName }}</div>
            </n-grid-item>
            <n-grid-item>
              <div class="meta-label">Poll interval</div>
              <div class="meta-value">{{ formatPollInterval(source?.poll_interval_s) }}</div>
            </n-grid-item>
            <n-grid-item>
              <div class="meta-label">Last success</div>
              <div class="meta-value">{{ formatTimestamp(source?.last_success_ts) }}</div>
            </n-grid-item>
            <n-grid-item>
              <div class="meta-label">Last error</div>
              <div class="meta-value">{{ source?.last_error || '—' }}</div>
            </n-grid-item>

            <template v-if="isHaSource">
              <n-grid-item>
                <div class="meta-label">Camera entity</div>
                <div class="meta-value">{{ source?.config?.camera_entity_id || '—' }}</div>
              </n-grid-item>
              <n-grid-item>
                <div class="meta-label">Flash entity</div>
                <div class="meta-value">{{ source?.config?.flash_entity_id || '—' }}</div>
              </n-grid-item>
              <n-grid-item>
                <div class="meta-label">Flash delay</div>
                <div class="meta-value">{{ formatMs(source?.config?.flash_delay_ms) }}</div>
              </n-grid-item>
            </template>

            <template v-if="isHttpSource">
              <n-grid-item>
                <div class="meta-label">Image URL</div>
                <div class="meta-value">{{ source?.config?.url || '—' }}</div>
              </n-grid-item>
              <n-grid-item>
                <div class="meta-label">Headers</div>
                <div class="meta-value">{{ formatHeaders(source?.config?.headers) }}</div>
              </n-grid-item>
              <n-grid-item>
                <div class="meta-label">Body</div>
                <div class="meta-value">{{ source?.config?.body || '—' }}</div>
              </n-grid-item>
            </template>
          </n-grid>
        </template>
      </div>
    </n-collapse-transition>
  </n-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import {
  NCard,
  NIcon,
  NTag,
  NButton,
  NCollapseTransition,
  NGrid,
  NGridItem,
  NForm,
  NFormItemGi,
  NInput,
  NSelect,
  NInputNumber,
  NSwitch,
  NSpace,
  NText,
  useMessage
} from 'naive-ui';
import {
  EditOutlined,
  ExpandMoreOutlined,
  HomeOutlined,
  AutoFixHighOutlined,
  PublicFilled,
  WifiTetheringOutlined,
  HelpOutlineOutlined
} from '@vicons/material';
import { apiService } from '@/services/api';
import { getSourceColor, getSourceLabel, normalizeSourceType } from '@/utils/sourceMeta';

const props = defineProps({
  source: { type: Object, default: null }
});

const emit = defineEmits(['updated']);
const message = useMessage();

const expanded = ref(false);
const editing = ref(false);
const saving = ref(false);
const loadingCameras = ref(false);
const cameras = ref([]);

const sourceType = computed(() => normalizeSourceType(props.source?.source_type));
const sourceColor = computed(() => getSourceColor(sourceType.value));
const sourceTitle = computed(() => getSourceLabel(sourceType.value));
const sourceName = computed(() => props.source?.name || 'Unknown');
const sourceEnabled = computed(() => props.source?.enabled === 1 || props.source?.enabled === true);
const isHaSource = computed(() => sourceType.value === 'ha_camera');
const isHttpSource = computed(() => sourceType.value === 'http');
const canEdit = computed(() => !!props.source?.id);
const showPollInterval = computed(() => props.source?.poll_interval_s !== null && props.source?.poll_interval_s !== undefined);

const sourceIcon = computed(() => {
  if (sourceType.value === 'mqtt') return WifiTetheringOutlined;
  if (sourceType.value === 'ha_camera') return HomeOutlined;
  if (sourceType.value === 'http') return PublicFilled;
  return HelpOutlineOutlined;
});

const form = ref({
  enabled: true,
  poll_interval_m: null,
  camera_entity_id: '',
  flash_enabled: false,
  flash_entity_id: '',
  flash_delay_ms: 10000,
  http_url: '',
  http_headers: '',
  http_body: ''
});

const parseHeaders = (raw) => {
  if (!raw || !raw.trim()) return null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed;
    }
  } catch (e) {
    return { __invalid__: true };
  }
  return { __invalid__: true };
};

const cameraOptions = computed(() => {
  const options = cameras.value.map((camera) => ({
    label: camera.name || camera.entity_id,
    value: camera.entity_id
  }));
  if (form.value.camera_entity_id && !options.find((opt) => opt.value === form.value.camera_entity_id)) {
    options.unshift({
      label: form.value.camera_entity_id,
      value: form.value.camera_entity_id
    });
  }
  return options;
});

const suggestedFlash = computed(() => {
  const selected = cameras.value.find((camera) => camera.entity_id === form.value.camera_entity_id);
  return selected?.suggested_flash_entity_id || null;
});

const useSuggestedFlash = () => {
  if (suggestedFlash.value) {
    form.value.flash_entity_id = suggestedFlash.value;
    form.value.flash_enabled = true;
  }
};

const syncForm = () => {
  const source = props.source;
  form.value = {
    enabled: source?.enabled === 1 || source?.enabled === true,
    poll_interval_m: source?.poll_interval_s ? Math.round(source.poll_interval_s / 60) : null,
    camera_entity_id: source?.config?.camera_entity_id || '',
    flash_enabled: !!source?.config?.flash_entity_id,
    flash_entity_id: source?.config?.flash_entity_id || '',
    flash_delay_ms: source?.config?.flash_delay_ms ?? 10000,
    http_url: source?.config?.url || '',
    http_headers: source?.config?.headers ? JSON.stringify(source.config.headers, null, 2) : '',
    http_body: source?.config?.body || ''
  };
};

watch(
  () => props.source,
  () => syncForm(),
  { immediate: true, deep: true }
);

const loadCameras = async () => {
  if (!isHaSource.value) return;
  loadingCameras.value = true;
  try {
    const result = await apiService.getJson('api/ha/cameras');
    cameras.value = result.cameras || [];
  } catch (e) {
    cameras.value = [];
    message.error('Failed to load camera list');
  } finally {
    loadingCameras.value = false;
  }
};

const toggleExpanded = () => {
  expanded.value = !expanded.value;
  if (expanded.value && editing.value) {
    loadCameras();
  }
};

const toggleEditing = () => {
  if (!canEdit.value) return;
  editing.value = !editing.value;
  expanded.value = true;
  if (editing.value) {
    loadCameras();
  }
};

const cancelEditing = () => {
  editing.value = false;
  syncForm();
};

const buildConfigPayload = () => {
  if (isHaSource.value) {
    const payload = {
      ...(props.source?.config || {}),
      camera_entity_id: form.value.camera_entity_id || props.source?.config?.camera_entity_id
    };
    if (form.value.flash_enabled) {
      payload.flash_entity_id = form.value.flash_entity_id || null;
      payload.flash_delay_ms = form.value.flash_delay_ms;
    } else {
      payload.flash_entity_id = null;
    }
    return payload;
  }
  if (isHttpSource.value) {
    const headers = parseHeaders(form.value.http_headers);
    if (headers && headers.__invalid__) {
      message.error('Headers must be valid JSON object (e.g. {"Authorization": "Bearer ..."}).');
      return { __invalid__: true };
    }
    return {
      ...(props.source?.config || {}),
      url: form.value.http_url?.trim() || props.source?.config?.url,
      headers: headers || null,
      body: form.value.http_body?.trim() || null
    };
  }
  return undefined;
};

const saveChanges = async () => {
  if (!canEdit.value) return;
  saving.value = true;
  try {
    const payload = {
      enabled: form.value.enabled,
      poll_interval_s: form.value.poll_interval_m ? form.value.poll_interval_m * 60 : null
    };
    const configPayload = buildConfigPayload();
    if (configPayload && configPayload.__invalid__) {
      saving.value = false;
      return;
    }
    if (configPayload !== undefined) {
      payload.config = configPayload;
    }
    await apiService.put(`api/sources/${props.source.id}`, payload);
    message.success('Source updated');
    editing.value = false;
    emit('updated');
  } catch (e) {
    message.error(`Update failed: ${e.message || e}`);
  } finally {
    saving.value = false;
  }
};

const formatTimestamp = (value) => {
  if (!value) return '—';
  const date = new Date(value);
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  }) + ' · ' + date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit'
  });
};

const formatPollInterval = (value) => {
  if (!value) return '—';
  const minutes = Math.round(value / 60);
  return `${minutes} min`;
};

const formatMs = (value) => {
  if (value === null || value === undefined) return '—';
  return `${value} ms`;
};

const formatHeaders = (headers) => {
  if (!headers) return '—';
  try {
    return JSON.stringify(headers);
  } catch (e) {
    return '—';
  }
};
</script>

<style scoped>
.source-collapse {
  width: 100%;
  border-left: 4px solid var(--source-color);
}

.source-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
}

.source-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.source-title {
  display: flex;
  flex-direction: column;
}

.source-name {
  font-weight: 600;
}

.source-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chevron {
  transition: transform 0.2s ease;
  opacity: 0.7;
}

.chevron.open {
  transform: rotate(180deg);
}

.source-body {
  margin-top: 12px;
}

.meta-label {
  font-size: 12px;
  opacity: 0.7;
}

.meta-value {
  font-size: 14px;
  font-weight: 600;
  word-break: break-word;
}

.code-inline {
  font-family: monospace, monospace;
  padding: 2px 6px;
  border-radius: 6px;
  background-color: rgba(255, 255, 255, 0.08);
}

.light-mode .code-inline {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>
