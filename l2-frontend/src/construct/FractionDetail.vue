<template>
  <div class="fraction-detail">
    <label>По умолчанию</label>
    <input class="form-control">
  </div>
</template>

<script setup lang="ts">

import {
  onMounted,
  ref, watch,
} from 'vue';
// import Treeselect from '@riophae/vue-treeselect';

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
});

const fraction = ref({});

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
.fraction-detail {
  background-color: #fff;
  border-radius: 4px;
  overflow-y: auto;
}
</style>
