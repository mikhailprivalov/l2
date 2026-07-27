<template>
  <div class="three-col">
    <div class="panel panel-nav">
      <div
        v-for="button in navButtons"
        :key="button.id"
        class="row-border"
      >
        <button
          class="transparent-button"
          :class="{ 'active-button': selectedNavId === button.id }"
          type="button"
          @click="selectedNavId = button.id"
        >
          {{ button.title }}
        </button>
      </div>
    </div>
    <div class="panel panel-middle" />
    <div class="panel panel-main" />
  </div>
</template>

<script setup lang="ts">
import {
  onMounted,
  ref,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';

interface NavButton {
  id: string;
  title: string;
}

const store = useStore();
const navButtons = ref<NavButton[]>([]);
const selectedNavId = ref<string | null>(null);

const loadNavButtons = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const { result } = await api('construct/dou/get-nav-buttons');
    navButtons.value = result || [];
    if (navButtons.value.length > 0 && !selectedNavId.value) {
      selectedNavId.value = navButtons.value[0].id;
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

onMounted(() => {
  loadNavButtons();
});
</script>

<style scoped lang="scss">
.three-col {
  display: grid;
  grid-template-columns: 1fr 1fr 5.56fr;
  height: calc(100vh - 36px);
  margin-bottom: 5px;
}

.panel {
  display: flex;
  flex-direction: column;
  background-color: #f8f7f7;
  border-right: 1px solid #b1b1b1;
  overflow-y: auto;
}

.panel-main {
  border-right: none;
}

.row-border {
  border-bottom: 1px solid #b1b1b1;
  display: flex;
}

.row-border:first-child {
  border-top: 1px solid #b1b1b1;
}

.transparent-button {
  background-color: transparent;
  color: #434A54;
  flex: 1;
  border: none;
  padding: 6px 10px;
  text-align: left;
  cursor: pointer;
}

.transparent-button:hover {
  background-color: #434a54;
  color: #FFFFFF;
}

.transparent-button:active {
  background-color: #37BC9B;
  color: #FFFFFF;
}

.active-button {
  background-color: #049372;
  color: #FFFFFF;
}
</style>
