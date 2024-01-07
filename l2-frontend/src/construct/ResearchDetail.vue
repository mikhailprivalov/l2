<template>
  <div>
    <h4 class="header">
      Редактирование анализа - {{ researchShortTitle }}
    </h4>
    <div class="research-detail">
      <div>
        <div class="margin">
          <label
            for="title"
            class="research-detail-label"
          >Полное наименование</label>
          <input
            id="title"
            v-model="research.title"
            class="form-control"
          >
        </div>
        <div class="margin">
          <label
            for="shortTitle"
            class="research-detail-label"
          >Краткое наименование</label>
          <input
            id="shortTitle"
            v-model="research.shortTitle"
            class="form-control"
          >
        </div>
      </div>
      <div class="code">
        <div class="margin height">
          <label
            for="code"
            class="research-detail-label"
          >Код НМУ</label>
          <input
            id="code"
            v-model="research.code"
            class="form-control"
          >
        </div>
        <div class="margin height">
          <label
            for="ecpCode"
            class="research-detail-label"
          >Код ЕЦП</label>
          <input
            id="ecpCode"
            v-model="research.ecpCode"
            class="form-control"
          >
        </div>
        <div class="margin height">
          <label
            for="internalCode"
            class="research-detail-label"
          >Код внутренний</label>
          <input
            id="internalCode"
            v-model="research.internalCode"
            class="form-control"
          >
        </div>
      </div>
      <div>
        <div class="margin">
          <label
            for="preparation"
            class="research-detail-label"
          >Подготовка</label>
          <textarea
            id="preparation"
            class="form-control"
            style="height: 90px"
            rows="4"
          />
        </div>
      </div>
    </div>
    <div class="research-fractions">
      <p></p>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, onMounted, ref, watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

const store = useStore();

const props = defineProps({
  researchPk: {
    type: Number,
    required: true,
  },
});

interface researchData {
  pk: number | null,
  title: string | null,
  shortTitle: string | null,
  code: number | null,
  internalCode: number | null,
  ecpCode: number | null,
  preparation: string | null,
}
const researchShortTitle = ref('');

const root = getCurrentInstance().proxy.$root;
const research = ref<researchData>({
  pk: -1,
  title: '',
  shortTitle: '',
  code: -1,
  internalCode: -1,
  ecpCode: -1,
  preparation: '',
});

const getResearch = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('laboratory/construct/get-research', { researchPk: props.researchPk });
  await store.dispatch(actions.DEC_LOADING);
  research.value = result;
  researchShortTitle.value = research.value?.title;
};

watch(() => props.researchPk, () => {
  getResearch();
});

onMounted(() => {
  getResearch();
});
</script>

<style scoped lang="scss">
.research-detail {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  margin: 0 20px;
}
.code {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}
.margin {
  margin: 0 5px;
}
.research-detail-label {
  margin-bottom: 0;
  margin-left: 12px;
}
.height {
  height: 55px;
}
.header {
  margin: 10px 0 10px 37px;
}
</style>
