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
        <div>
          <label>Название</label>
          <input class="form-control">
        </div>
        <button class="btn btn-blue-nb button-row">
          {{ selectedComplex ? 'Сохранить' : 'Создать' }}
        </button>
      </div>
    </div>
    <div
      v-if="selectedComplex"
      class="block shadow"
    >
      <h4>Список услуг в комплексе</h4>
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
import { onMounted, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';
import api from '@/api';

const store = useStore();

const selectedComplex = ref(null);
const complexs = ref([]);
const getComplexs = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/complex/get-complexs');
  await store.dispatch(actions.DEC_LOADING);
  complexs.value = result;
};

onMounted(() => {
  getComplexs();
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
  gap: 10px;
  margin-bottom: 2px;
}
.button-row {
  margin-top: 25px;
}
.margin-bottom {
  margin-bottom: 20px;
}
</style>
