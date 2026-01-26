<template>
  <n-flex>
    <router-link to="/">
      <n-button quaternary round size="large" style="padding: 0; font-size: 16px;">
        ← Back
      </n-button>
    </router-link>
    <img src="@/assets/logo.png" alt="Logo" style="max-width: 100px; margin-left: 20px;" class="theme-revert"/>
    <n-button :loading="loading" @click="loadMeter" round size="large" style="margin-left: 20px;">
      Refresh
    </n-button>
  </n-flex>
  <br />

  <template v-if="isMobile">
    <n-tabs type="line" animated>
      <n-tab-pane name="details" tab="Details">
        <MeterDetails
          :data="data"
          :settings="settings"
          :id="id"
          :downloadingDataset="downloadingDataset"
          @resetToSetup="resetToSetup"
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
    <n-grid cols="12">
      <n-gi span="2" >
        <MeterDetails
          :data="data"
          :settings="settings"
          :id="id"
          :downloadingDataset="downloadingDataset"
          @resetToSetup="resetToSetup"
          @deleteMeter="deleteMeter"
          @clearEvaluations="clearEvaluations"
          @downloadDataset="downloadDataset"
          @deleteDataset="deleteDataset"
        />
      </n-gi>
      <n-gi span="7" style="padding-left: 20px; padding-right: 10px;" v-if="evaluations !== null">
        <EvaluationResultList :evaluations="evaluations" :name="id" @load-more="loadMoreEvaluations" @dataset-uploaded="loadMeter"/>
      </n-gi>
      <n-gi span="3" style="max-width: 500px;">
        <MeterCharts :history="history" />
      </n-gi>
    </n-grid>
  </template>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import router from '@/router';
import EvaluationResultList from "@/components/EvaluationResultList.vue";
import MeterDetails from "@/components/MeterDetails.vue";
import MeterCharts from "@/components/MeterCharts.vue";
import {NFlex, NButton, NGrid, NGi, NTabs, NTabPane} from "naive-ui";
import { useWatermeterStore } from '@/stores/watermeterStore';
import { storeToRefs } from 'pinia';

const route = useRoute();
const id = route.params.id;
const store = useWatermeterStore();
const { lastPicture: data, evaluations, history, settings } = storeToRefs(store);

const loading = ref(false);
const downloadingDataset = ref(false);
const isMobile = ref(window.innerWidth < 1000);

const updateWidth = () => {
  isMobile.value = window.innerWidth < 800;
};

onMounted(() => {
  window.addEventListener('resize', updateWidth);
  loadMeter();
});

onUnmounted(() => {
  window.removeEventListener('resize', updateWidth);
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
.bg {
  background-color: rgba(240, 240, 240, 0.1);
  padding: 20px;
  border-radius: 15px;
  margin-bottom: 15px;
}
</style>
