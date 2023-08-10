<script setup lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import {
  computed, getCurrentInstance, ref, watch,
} from 'vue';

import useApi, { ApiStatus } from '@/api/useApi';
import api from '@/api';
import * as actions from '@/store/action-types';
import Spinner from '@/components/Spinner.vue';
import ColorTitled from '@/ui-cards/ColorTitled.vue';
import { useStore } from '@/store';

const root = getCurrentInstance().proxy.$root;

const tubeRelatedId = computed(() => root.$route.params.id);

const apiParams = computed(() => ({
  path: 'researches/tube-related-data',
  data: {
    id: tubeRelatedId.value,
  },
}));

type Tube = {color: string, title: string, pk: number};

interface ApiType {
  maxResearchesPerTube: number,
  researches: string[],
  tubes: Tube[],
  type: number | null,
}

const defaultData = (): ApiType => ({
  maxResearchesPerTube: null,
  researches: [],
  tubes: [],
  type: null,
});

const {
  data,
  status,
} = useApi<ApiType>(apiParams, { defaultData });

const selectedTubeTypeId = ref(data.value.type);

watch(() => data.value.type, () => {
  selectedTubeTypeId.value = data.value.type;
});

const maxResearchesPerTube = ref(data.value.maxResearchesPerTube);

watch(data, () => {
  maxResearchesPerTube.value = data.value.maxResearchesPerTube;
});

const store = useStore();

const save = async () => {
  await store.dispatch(actions.INC_LOADING);
  await api('researches/tube-related-data/update', {
    id: tubeRelatedId.value,
    maxResearchesPerTube: maxResearchesPerTube.value,
    type: selectedTubeTypeId.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  root.$ok('Сохранено');
};
</script>

<template>
  <div :class="$style.root">
    <Spinner v-if="status !== ApiStatus.SUCCESS" />
    <div v-else>
      <div :class="$style.tube">
        <Treeselect
          v-model="selectedTubeTypeId"
          :options="data.tubes"
          :multiple="false"
        >
          <template #value-label="{ node }">
            <ColorTitled
              :color="node.raw?.color || '#fff'"
              :title="node.raw?.label || '-'"
            />
          </template>
          <template #option-label="{ node }">
            <ColorTitled
              :color="node.raw?.color || '#fff'"
              :title="node.raw?.label || '-'"
            />
          </template>
        </Treeselect>
      </div>
      <div>
        <strong>Исследования:</strong>
      </div>
      <ul>
        <li
          v-for="research in data.researches"
          :key="research"
        >
          {{ research }}
        </li>
      </ul>
      <div :class="$style.form">
        <div class="input-group treeselect-noborder-left">
          <span class="input-group-addon">Макc. кол-во исследований на одну ёмкость</span>
          <input
            v-model="maxResearchesPerTube"
            class="form-control"
            type="number"
            min="1"
            max="1000"
            step="1"
            placeholder="пусто для неограниченного количества"
          >
        </div>

        <button
          type="button"
          class="btn btn-blue-nb"
          :class="$style.saveButton"
          @click="save"
        >
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<style module lang="scss">
.root {
  padding: 10px;
  max-width: 700px;
}

.tube {
  padding: 2px;
  margin-bottom: 10px;
  font-size: 10pt;
  border: none;
  border-radius: 4px;
  color: #434A54;
  background-color: #FFF;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.form {
  padding: 10px 0;
}

.saveButton {
  margin-top: 15px;
}
</style>
