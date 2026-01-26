<template>
  <div class="dataset-uploader">
    <div v-if="items.length === 0">No images provided.</div>

    <div v-for="(item, i) in items" :key="i" class="row">
      <div class="previews">
        <div class="preview">
          <img :src="`data:image/png;base64,${item.colored}`" alt="colored" style="max-height: 32px; width: auto; "/>
        </div>
        <div class="preview">
          <img :src="`data:image/png;base64,${item.thresholded}`" alt="thresholded" style="max-height: 32px; width: auto;"/>
        </div>
      </div>

      <div class="controls">
        <n-radio-group v-model:value="selections[i]" name="radiobuttongroup1">
          <n-radio-button
            v-for="opt in options"
            :key="opt.value"
            :value="opt.value"
            :label="opt.label"
          />
        </n-radio-group>
      </div>
    </div>

    <div class="actions">
      <n-button @click="upload" :disabled="uploading || items.length === 0">Upload selected</n-button>
      <span class="status">{{ status }}</span>
    </div>
  </div>
</template>

<script setup>
import {ref, computed, watchEffect} from 'vue'
import { NRadioGroup, NRadioButton, NButton } from 'naive-ui'
import {apiService} from "@/services/api";

const props = defineProps({
  colored: { type: Array, required: true },
  thresholded: { type: Array, required: true },
  name: { type: String, required: true },
  setvalues: { type: Array, required: true },
  onClose: { type: Function, default: null },
  onUploaded: { type: Function, default: null }
})

// build items array from props
const items = computed(() => {
  const len = Math.min(props.colored.length, props.thresholded.length)
  const arr = []
  for (let i = 0; i < len; i++) {
    arr.push({ colored: props.colored[i], thresholded: props.thresholded[i] })
  }
  return arr
})

// default selection is 'skip' (do not send)
const selections = ref( props.setvalues && props.setvalues.length === items.value.length
  ? props.setvalues.slice()
  : Array(items.value.length).fill('skip')
)

// keep selections length in sync when items change
watchEffect(() => {
  console.log(props.setvalues)
  if (selections.value.length < items.value.length) {
    selections.value = selections.value.concat(Array(items.value.length - selections.value.length).fill('skip'))
  } else if (selections.value.length > items.value.length) {
    selections.value = selections.value.slice(0, items.value.length)
  }
})

const options = [
  { label: '🚫', value: 'skip' },
  ...Array.from({ length: 10 }).map((_, i) => ({ label: String(i), value: String(i) })),
  { label: '↕', value: 'r' }
]

const uploading = ref(false)
const status = ref('')

async function upload() {
  const labels = []
  const colored = []
  const thresholded = []

  for (let i = 0; i < items.value.length; i++) {
    const sel = selections.value[i]
    if (sel && sel !== 'skip') {
      labels.push(sel)
      colored.push(items.value[i].colored)
      thresholded.push(items.value[i].thresholded)
    }
  }

  if (labels.length === 0) {
    status.value = 'No images selected for upload.'
    return
  }

  const payload = {
    name: props.name,
    labels,
    colored,
    thresholded
  }

  uploading.value = true
  status.value = 'Uploading...'
  try {
    const headers = { 'Content-Type': 'application/json' }
    if (localStorage.getItem('secret')) headers['secret'] = localStorage.getItem('secret')

    const res = await apiService.post("api/dataset/upload", payload)

    if (!res.ok) {
      const text = await res.text()
      status.value = `Upload failed: ${res.status} ${text}`
    } else {
      const j = await res.json()
      status.value = `Saved ${j.saved} images to ${j.output_root}`
      if (props.onUploaded) {
        props.onUploaded()
      }
      if (props.onClose) {
        setTimeout(() => props.onClose(), 500)
      }
    }
  } catch (err) {
    status.value = `Upload error: ${err.message || err}`
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.dataset-uploader {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 6px;
}
.previews {
  display: flex;
  gap: 8px;
}
.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.status {
  color: #666;
}
</style>

