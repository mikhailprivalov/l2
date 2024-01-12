<template>
  <div class="main">
    <div class="fraction-detail">
      <h6>Фракция - {{ fraction.title }}</h6>
      <label>Варианты</label>
      <Treeselect
        v-model="fraction.variantsId"
        :options="props.variants"
      />
      <label>Формула</label>
      <input
        v-model="fraction.formula"
        class="form-control"
      >
      <div>
        <label>Рефернсы М</label>
        <input class="form-control">
        <input class="form-control">
        <button class="btn btn-blue-nb">
          Добавить
        </button>
      </div>
      <div>
        <label>Рефернсы Ж</label>
        <input class="form-control">
        <input class="form-control">
        <button class="btn btn-blue-nb">
          Добавить
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import {
  onMounted,
  ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import * as actions from '@/store/action-types';
import api from '@/api';
import { useStore } from '@/store';

const store = useStore();
const props = defineProps({
  fractionPk: {
    type: Number,
    required: true,
  },
  variants: {
    type: Array,
    required: true,
  },
});

interface otherFractionData {
  pk: number | null,
  title: string,
  variantsId: number | null,
  formula: string,
  refM: any,
  refF: any,
}

const fraction = ref<otherFractionData>({
  pk: null,
  title: '',
  variantsId: null,
  formula: '',
  refM: [],
  refF: [],
});

const getFraction = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-fraction', { fractionPk: props.fractionPk });
  await store.dispatch(actions.DEC_LOADING);
  fraction.value = result;
};

watch(() => [props.fractionPk], () => {
  getFraction();
});

onMounted(() => {
  getFraction();
});
</script>

<style scoped lang="scss">
.main {
  border-left: 1px solid #b1b1b1;
  margin-left: 10px;
  margin-bottom: 10px;
  padding-left: 10px;
}
.fraction-detail {
  height: 100%;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
  padding: 10px 5px 10px 5px;
}
</style>
