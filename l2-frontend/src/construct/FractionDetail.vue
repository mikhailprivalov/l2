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

</script>

<style scoped lang="scss">

</style>
