<template>
  <div ref="container" class="template-editor">
    <img :src="imageSrc" alt="Template" @load="onImageLoad" />
    <svg class="template-overlay" viewBox="0 0 1 1" preserveAspectRatio="none">
      <polygon
        v-if="normalizedPoints.length === 4"
        :points="polygonPoints"
        class="template-polygon"
      />
    </svg>
    <div
      v-for="(point, index) in normalizedPoints"
      :key="index"
      class="template-point"
      :class="{ primary: index === 0 }"
      :style="pointStyle(point)"
      @pointerdown="startDrag(index, $event)"
    >
      <span class="point-label">{{ index === 0 ? 'TL' : index + 1 }}</span>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch, computed } from 'vue';

const props = defineProps({
  imageSrc: { type: String, required: true },
  points: { type: Array, default: () => [] }
});

const emit = defineEmits(['update:points']);
const container = ref(null);
const containerSize = ref({ width: 0, height: 0 });
const normalizedPoints = ref([]);
const draggingIndex = ref(null);
let resizeObserver = null;

const defaultPoints = () => ([
  { x: 0.2, y: 0.2 },
  { x: 0.8, y: 0.2 },
  { x: 0.8, y: 0.8 },
  { x: 0.2, y: 0.8 }
]);

const clamp = (value) => Math.max(0, Math.min(1, Number(value) || 0));

const syncPoints = (incoming) => {
  if (incoming && incoming.length === 4) {
    normalizedPoints.value = incoming.map((p) => ({
      x: clamp(p.x ?? p[0]),
      y: clamp(p.y ?? p[1])
    }));
  } else if (normalizedPoints.value.length === 0) {
    normalizedPoints.value = defaultPoints();
    emit('update:points', normalizedPoints.value);
  }
};

watch(
  () => props.points,
  (next) => syncPoints(next),
  { immediate: true, deep: true }
);

const polygonPoints = computed(() =>
  normalizedPoints.value.map((p) => `${p.x},${p.y}`).join(' ')
);

const pointStyle = (point) => {
  const points = normalizedPoints.value;
  const center = points.length
    ? points.reduce((acc, p) => ({ x: acc.x + p.x / points.length, y: acc.y + p.y / points.length }), { x: 0, y: 0 })
    : { x: 0.5, y: 0.5 };
  const dx = point.x - center.x;
  const dy = point.y - center.y;
  const len = Math.hypot(dx, dy) || 1;
  const offset = 10;
  let offsetX = (dx / len) * offset;
  let offsetY = (dy / len) * offset;
  const width = containerSize.value.width;
  const height = containerSize.value.height;
  const handleRadius = 8;
  if (width && height) {
    const baseX = point.x * width;
    const baseY = point.y * height;
    const clampPixel = (value, min, max) => Math.min(max, Math.max(min, value));
    const clampedX = clampPixel(baseX + offsetX, handleRadius, width - handleRadius);
    const clampedY = clampPixel(baseY + offsetY, handleRadius, height - handleRadius);
    offsetX = clampedX - baseX;
    offsetY = clampedY - baseY;
  } else {
    if (point.x <= 0.03 && offsetX < 0) offsetX = 0;
    if (point.x >= 0.97 && offsetX > 0) offsetX = 0;
    if (point.y <= 0.03 && offsetY < 0) offsetY = 0;
    if (point.y >= 0.97 && offsetY > 0) offsetY = 0;
  }
  return {
    left: `${point.x * 100}%`,
    top: `${point.y * 100}%`,
    transform: `translate(-50%, -50%) translate(${offsetX}px, ${offsetY}px)`
  };
};

const onImageLoad = () => {
  if (normalizedPoints.value.length === 0) {
    syncPoints([]);
  }
  updateContainerSize();
};

const updateContainerSize = () => {
  if (!container.value) return;
  const rect = container.value.getBoundingClientRect();
  containerSize.value = { width: rect.width, height: rect.height };
};

const startDrag = (index, event) => {
  draggingIndex.value = index;
  event.preventDefault();
  window.addEventListener('pointermove', onDrag);
  window.addEventListener('pointerup', stopDrag);
};

const onDrag = (event) => {
  if (draggingIndex.value === null || !container.value) return;
  const rect = container.value.getBoundingClientRect();
  const x = clamp((event.clientX - rect.left) / rect.width);
  const y = clamp((event.clientY - rect.top) / rect.height);
  normalizedPoints.value = normalizedPoints.value.map((point, idx) =>
    idx === draggingIndex.value ? { x, y } : point
  );
  emit('update:points', normalizedPoints.value);
};

const stopDrag = () => {
  draggingIndex.value = null;
  window.removeEventListener('pointermove', onDrag);
  window.removeEventListener('pointerup', stopDrag);
};

onMounted(() => {
  updateContainerSize();
  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(updateContainerSize);
    if (container.value) {
      resizeObserver.observe(container.value);
    }
  } else {
    window.addEventListener('resize', updateContainerSize);
  }
});

onBeforeUnmount(() => {
  stopDrag();
  if (resizeObserver && container.value) {
    resizeObserver.unobserve(container.value);
  }
  window.removeEventListener('resize', updateContainerSize);
});

</script>

<style scoped>
.template-editor {
  position: relative;
  width: 100%;
}

.template-editor img {
  width: 100%;
  display: block;
}

.template-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.template-polygon {
  fill: rgba(255, 80, 80, 0.15);
  stroke: rgba(255, 80, 80, 0.8);
  stroke-width: 0.004;
}

.template-point {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(30, 30, 30, 0.8);
  border: 2px solid rgba(255, 255, 255, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  z-index: 2;
}

.template-point.primary {
  background: rgba(220, 60, 60, 0.9);
  border-color: rgba(255, 255, 255, 0.95);
}

.point-label {
  font-size: 8px;
  color: #fff;
  font-weight: 700;
}
</style>
