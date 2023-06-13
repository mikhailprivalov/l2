<script setup lang="ts">
import {
  computed, getCurrentInstance, ref, watch,
} from 'vue';

import useApi, { ApiStatus } from '@/api/useApi';

const root = getCurrentInstance().proxy.$root;

const tubeRelatedId = computed(() => root.$router.params.id);

const apiParams = computed(() => ({
  path: 'researches/tube-related-data',
  data: {
    id: tubeRelatedId.value,
  },
}));

interface ApiType {
  maxResearchesPerTube: number,
}

const defaultData = (): ApiType => ({
  maxResearchesPerTube: null,
});

const {
  data,
  status,
  call,
} = useApi<ApiType>(apiParams, { defaultData });
</script>

<template>
  <div>
    TODO
  </div>
</template>

<style scoped lang="scss">

</style>
