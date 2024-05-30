<template>
  <div>
    <Treeselect
      v-model="selectedComplex"
      :options="complexs"
      class="margin-bottom"
      placeholder="Выберите комплексную услугу"
    />
    <div class="block shadow">
      <div class="edit-complex">
        <div class="edit-complex-title">
          <input class="form-control nbr">
        </div>
        <button
          v-tippy
          class="btn last btn-blue-nb nbr"
          :title="complexIsHidden ? 'Показать': 'Скрыть'"
        >
          <i :class="complexIsHidden ? 'fa fa-eye' : 'fa fa-times'" />
        </button>
        <button class="btn btn-blue-nb nbr">
          {{ selectedComplex ? 'Сохранить' : 'Создать' }}
        </button>
      </div>
    </div>
    <div
      v-if="selectedComplex"
      class="block shadow"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col>
            <col width="35">
          </colgroup>
          <tr
            v-for="service in servicesInComplex"
            :key="service.id"
          >
            <VueTippyTd
              class="research border padding-left"
              :text="service.label"
            />
            <td>
              <div class="button">
                <button class="btn btn-blue-nb btn-flex">
                  <i :class="service.hide ?'fa fa-eye' : 'fa fa-times'" />
                </button>
              </div>
            </td>
          </tr>
          <tr
            v-if="servicesInComplex.length === 0"
            class="text-center"
          >
            <td>
              Нет данных
            </td>
          </tr>
        </table>
      </div>
    </div>
    <div
      v-if="selectedComplex"
      class="block shadow"
    >
      <h4>Добавление услуги в комплекс</h4>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';
import api from '@/api';
import VueTippyTd from '@/construct/VueTippyTd.vue';

const store = useStore();

const selectedComplex = ref(null);
const complexs = ref([]);
const hiddenStatus = ref(false);

const complexIsHidden = computed(() => hiddenStatus.value);

const getComplexs = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/complex/get-complexs');
  await store.dispatch(actions.DEC_LOADING);
  complexs.value = result;
};

onMounted(() => {
  getComplexs();
});

const servicesInComplex = ref([]);

const getServicesInComplex = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/complex/check-hidden', { complexId: selectedComplex.value });
  await store.dispatch(actions.DEC_LOADING);
  servicesInComplex.value = result;
};

const checkHidden = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/complex/check-hidden', { complexId: selectedComplex.value });
  await store.dispatch(actions.DEC_LOADING);
  hiddenStatus.value = result;
};

watch(selectedComplex, () => {
  if (selectedComplex.value) {
    checkHidden();
    getServicesInComplex();
  } else {
    servicesInComplex.value = [];
    hiddenStatus.value = false;
  }
});

</script>

<style scoped lang="scss">
.shadow {
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
}
.block {
  background-color: #fff;
  border-radius: 5px;
  margin-bottom: 20px;
  padding: 2px;
}
.edit-complex {
  display: flex;
}
.edit-complex-title {
  flex-grow: 1;
}
.margin-bottom {
  margin-bottom: 20px;
}
.scroll {
  min-height: 112px;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
  .btn-flex {
    align-self: stretch;
    flex: 1;
    padding: 7px 0;
  }

</style>
