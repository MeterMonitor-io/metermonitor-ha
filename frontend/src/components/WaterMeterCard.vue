
<template>
  <n-card :title="meter_name" size="small" style="max-width: 300px;">
    <n-flex justify="space-around" size="small" v-if="last_digits" :size="[0,0]" class="theme-revert">
      <img :style="`width:calc(150px / ${last_digits.length});`" class="digit th" v-for="[i,base64] in last_digits.entries()" :key="i + 'c'" :src="'data:image/png;base64,' + base64" alt="D"/>
    </n-flex>
    <n-flex justify="space-evenly" size="large" v-if="last_result && last_digits">
      <span
          class="prediction google-sans-code"
          v-for="[i, digit] in (last_result + '').padStart(last_digits.length, '0').split('').entries()"
          :key="i + 'd'"
      >
        <template v-if="i === last_digits.length-4">
          {{ (digit[0][0]==='r')? '↕' : digit[0][0] }},
        </template>
        <div v-else-if="i > last_digits.length-4" style="color: #ff9a9a">
          {{ (digit[0][0]==='r')? '↕' : digit[0][0] }}
        </div>
        <template v-else>
          {{ (digit[0][0]==='r')? '↕' : digit[0][0] }}
        </template>

      </span>
    </n-flex>
    <n-flex justify="space-between">
    </n-flex>
    <template #header-extra>
      {{ last_updated_locale }}
    </template>
    <template #action>
      <n-flex justify="space-between">
        <WifiStatus :rssi="rssi" />
        <router-link v-if="setup" :to="'/setup/'+meter_name"><n-button round>Setup</n-button></router-link>
        <router-link v-else :to="'/meter/'+meter_name"><n-button round>View</n-button></router-link>
      </n-flex>
    </template>
  </n-card>
</template>

<script setup>
import {NCard, NButton, NFlex} from 'naive-ui';
import {defineProps} from 'vue';
import WifiStatus from "@/components/WifiStatus.vue";

const props = defineProps([
    'meter_name',
    'last_updated', // eg "2025-02-04T03:15:31"
    'setup',
    'last_digits',
    'last_result',
    'rssi'
]);

const last_updated_locale = new Date(props.last_updated).toLocaleString();
</script>

<style scoped>
.digit{
  mix-blend-mode: screen;
  opacity: 0.4;
}

.prediction{
  width: 16px;
  text-wrap: nowrap;
  font-size: 1.6em;
}
</style>