<template>
  <template v-if="isMobile">
    <n-tabs type="line" animated>
      <n-tab-pane name="details" tab="Details">
        <MeterDetails
          :data="data"
          :settings="settings"
          :id="id"
          :downloadingDataset="downloadingDataset"
          @resetToSetup="resetToSetup"
          @triggerCapture="triggerCapture"
          @deleteMeter="deleteMeter"
          @clearEvaluations="clearEvaluations"
          @downloadDataset="downloadDataset"
          @deleteDataset="deleteDataset"
        />
      </n-tab-pane>
      <n-tab-pane name="evaluations" tab="Evaluations">
        <div style="padding-left: 10px; padding-right: 10px;" v-if="evaluations !== null">
          <EvaluationResultList :evaluations="evaluations" :name="id" @load-more="loadMoreEvaluations" @dataset-uploaded="loadMeter"/>
        </div>
      </n-tab-pane>
      <n-tab-pane name="charts" tab="Charts">
        <MeterCharts :history="history" />
      </n-tab-pane>
    </n-tabs>
  </template>

  <template v-else>
    <div class="meter-layout">
      <aside class="meter-sidebar">
        <div class="sidebar-content">
          <MeterDetails
            :data="data"
            :settings="settings"
            :id="id"
            :downloadingDataset="downloadingDataset"
            :history="history"
            @resetToSetup="resetToSetup"
            @triggerCapture="triggerCapture"
            @deleteMeter="deleteMeter"
            @clearEvaluations="clearEvaluations"
            @downloadDataset="downloadDataset"
            @deleteDataset="deleteDataset"
          />
        </div>
      </aside>
      <main class="meter-content" v-if="evaluations !== null">
        <EvaluationResultList :evaluations="evaluations" :name="id" @load-more="loadMoreEvaluations" @dataset-uploaded="loadMeter"/>
      </main>
    </div>
  </template>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import router from '@/router';
import EvaluationResultList from "@/components/EvaluationResultList.vue";
import MeterDetails from "@/components/MeterDetails.vue";
import MeterCharts from "@/components/MeterCharts.vue";
import { NTabs, NTabPane, useMessage } from "naive-ui";
import { useWatermeterStore } from '@/stores/watermeterStore';
import { storeToRefs } from 'pinia';
import { useHeaderControls } from '@/composables/headerControls';

const route = useRoute();
const id = route.params.id;
const store = useWatermeterStore();
const { lastPicture: data, evaluations, history, settings } = storeToRefs(store);

const loading = ref(false);
const downloadingDataset = ref(false);
const isMobile = ref(window.innerWidth < 1000);
const headerControls = useHeaderControls();

const updateWidth = () => {
  isMobile.value = window.innerWidth < 800;
};

onMounted(() => {
  window.addEventListener('resize', updateWidth);
  loadMeter();
  if (headerControls) {
    headerControls.setHeader({
      showRefresh: true,
      onRefresh: loadMeter,
      refreshLoading: loading.value
    });
  }
});

onUnmounted(() => {
  window.removeEventListener('resize', updateWidth);
  if (headerControls) {
    headerControls.resetHeader();
  }
});

watch(loading, (next) => {
  if (!headerControls) return;
  headerControls.setHeader({ refreshLoading: next });
});

const host = import.meta.env.VITE_HOST;

const loadMeter = async () => {
  loading.value = true;
  try {
    await store.fetchAll(id);
  } catch (e) {
    if (e.response && e.response.status === 401) {
      router.push({ path: '/unlock' });
    }
  }
  loading.value = false;
};

const loadMoreEvaluations = async () => {
  if (!evaluations.value || evaluations.value.length === 0) return;
  const lastId = evaluations.value[evaluations.value.length - 1].id;
  await store.fetchEvaluations(id, 10, lastId);
};

const deleteMeter = async () => {
  let response = await fetch(host + 'api/watermeters/' + id, {
    method: 'DELETE',
    headers: { secret: localStorage.getItem('secret') }
  });
  if (response.status === 200) {
    router.replace({ path: '/' });
  } else {
    console.log('Error deleting meter');
  }
};

const resetToSetup = async () => {
  let response = await fetch(host + 'api/setup/' + id + '/enable', {
    method: 'POST',
    headers: { secret: localStorage.getItem('secret') }
  });
  if (response.status === 200) {
    router.replace({ path: '/setup/' + id });
  } else {
    console.log('Error resetting meter');
  }
};

const message = useMessage();

const triggerCapture = async () => {
  try {
    store.capturing = true;
    const response = await fetch(host + 'api/sources/' + store.source.id + '/capture', {
      method: 'POST',
      headers: { secret: localStorage.getItem('secret') }
    });
    store.capturing = false;

    if (response.status === 200) {
      console.log('Capture triggered successfully');
    } else {
      console.log('Error triggering capture');
      message.error('Error triggering capture: ' + (await response.json()).detail, {
        closable: true,
        duration: 60000
      });
    }

    // refresh meter data to get the new picture
    await loadMeter();
  } catch (err) {
    message.error('Error triggering capture: ' + err.message);
    console.log('Error triggering capture:', err);
    // get data from response and show error message
  }
};

const downloadDataset = async () => {
  downloadingDataset.value = true;
  try {
    const response = await fetch(host + 'api/dataset/' + id + '/download', {
      headers: { secret: localStorage.getItem('secret') }
    });

    if (response.status === 200) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${id}_dataset.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } else {
      console.log('Error downloading dataset');
    }
  } catch (err) {
    console.log('Error downloading dataset:', err);
  } finally {
    downloadingDataset.value = false;
  }
};

const deleteDataset = async () => {
  try {
    const response = await fetch(host + 'api/dataset/' + id, {
      method: 'DELETE',
      headers: { secret: localStorage.getItem('secret') }
    });

    if (response.status === 200) {
      // Reload meter data to update dataset_present status
      await loadMeter();
    } else {
      console.log('Error deleting dataset');
    }
  } catch (err) {
    console.log('Error deleting dataset:', err);
  }
};

const clearEvaluations = async () => {
  try {
    const response = await fetch(host + 'api/watermeters/' + id + '/evals', {
      method: 'DELETE',
      headers: { secret: localStorage.getItem('secret') }
    });

    if (response.status === 200) {
      const result = await response.json();
      console.log(`Cleared ${result.count} evaluations`);

      // Re-evaluate latest picture to restore state
      await fetch(host + 'api/watermeters/' + id + '/evaluations/reevaluate', {
        method: 'POST',
        headers: { secret: localStorage.getItem('secret') }
      });

      // Reload meter data to update evaluations
      await loadMeter();
    } else {
      console.log('Error clearing evaluations');
    }
  } catch (err) {
    console.log('Error clearing evaluations:', err);
  }
};
</script>

<style scoped>
.meter-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.meter-sidebar {
  width: 360px;
  flex: 0 0 360px;
  min-width: 360px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
}

.sidebar-content {
  width: 100%;
}

.meter-content {
  flex: 1;
  min-width: 0;
}

.light-mode .meter-sidebar {
  background: rgba(0, 0, 0, 0.04);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
}
</style>
