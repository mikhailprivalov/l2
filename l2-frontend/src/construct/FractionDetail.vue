<template>
  <div class="main">
    <div class="fraction-detail">
      <h6>Фракция - {{ fraction.title }}</h6>
      <label>По умолчанию</label>
      <input class="form-control">
      <label>Варианты</label>
      <Treeselect
        v-model="props.fraction.variantsId"
        :options="props.variants"
        :clearable="false"
        :append-to-body="true"
      />
      <label>Формула</label>
      <input
        v-model="props.fraction.formula"
        class="form-control"
      >
      <label>Рефернсы М</label>
      <div
        v-for="(refM, idx) in fraction.refM"
        :key="idx"
        class="flex"
      >
        <input
          v-model="refM.age"
          class="form-control"
        >
        <input
          v-model="refM.value"
          class="form-control"
        >
        <button
          class="btn btn-blue-nb"
          @click="deleteRef(idx, 'm')"
        >
          <i class="fa fa-times" />
        </button>
      </div>
      <div>
        <button
          class="btn btn-blue-nb"
          @click="addRef('m')"
        >
          Добавить
        </button>
      </div>
      <label>Рефернсы Ж</label>
      <div
        v-for="(refF, idx) in fraction.refF"
        :key="idx"
        class="flex"
      >
        <input
          v-model="refF.age"
          class="form-control"
        >
        <input
          v-model="refF.value"
          class="form-control"
        >
        <button
          class="btn btn-blue-nb"
          @click="deleteRef(idx, 'f')"
        >
          <i class="fa fa-times" />
        </button>
      </div>
      <div>
        <button
          class="btn btn-blue-nb"
          @click="addRef('f')"
        >
          Добавить
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import {
  getCurrentInstance,
  ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import * as actions from '@/store/action-types';
import api from '@/api';
import { useStore } from '@/store';

const store = useStore();
const props = defineProps({
  fraction: {
    type: Object,
    required: true,
  },
  variants: {
    type: Array,
    required: true,
  },
});

interface refData {
  age: string,
  value: string
}

interface otherFractionData {
  pk: number | null,
  title: string,
  variantsId: number | null,
  formula: string,
  refM: refData[],
  refF: refData[],
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
  // await store.dispatch(actions.INC_LOADING);
  // const { result } = await api('construct/laboratory/get-fraction', { fractionPk: props.fractionPk });
  // await store.dispatch(actions.DEC_LOADING);
  // fraction.value = result;
};

watch(() => [props.fraction], () => {
  if (props.fraction.length !== 0) {
    getFraction();
  }
}, { immediate: true });

const addRef = (refKey: string) => {
  if (refKey === 'm') {
    fraction.value.refM.push({ age: '', value: '' });
  } else {
    fraction.value.refF.push({ age: '', value: '' });
  }
};

const deleteRef = (idx: number, refKey: string) => {
  if (refKey === 'm') {
    fraction.value.refM.splice(idx, 1);
  } else {
    fraction.value.refF.splice(idx, 1);
  }
};
</script>

<style scoped lang="scss">
.main {
  border-left: 1px solid #b1b1b1;
  margin-left: 10px;
  padding-left: 10px;
  position: relative;
  overflow-y: auto;
}
.fraction-detail {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
  padding: 10px 5px 10px 5px;
  overflow-y: auto;
}
.flex {
  display: flex;
}
.flex-end {
  display: flex;
  justify-content: flex-end;
}
</style>
