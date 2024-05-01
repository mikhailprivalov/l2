<template>
  <div>
    <div class="main">
      <div class="company">
        <div class="margin-item">
          <RadioField
            v-model="selectedType"
            :variants="typesCompany"
            @modified="changeType"
          />
        </div>
        <div class="margin-item">
          <Treeselect
            v-model="selectedCompany"
            :options="companies"
            :normalizer="normalizer"
            :clearable="false"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import RadioField from '@/fields/RadioField.vue';
import * as actions from '@/store/action-types';
import api from '@/api';
import { useStore } from '@/store';

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const typesCompany = ref(['Заказчик', 'Внешний исполнитель', 'Работодатель']);
const selectedType = ref(null);

const companies = ref([]);
const getCompanies = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { data } = await api('get-companies', { selectedType: selectedType.value });
  await store.dispatch(actions.DEC_LOADING);
  companies.value = data;
};
const normalizer = (node) => ({
  id: node.pk,
  label: node.title,
});

const selectedCompany = ref(null);

const changeType = () => {
  selectedCompany.value = null;
  getCompanies();
};

</script>

<style scoped lang="scss">
.main {
  margin: 0 20px;
}
.company {
  width: 700px;
  margin: 0 auto;
}
.margin-item {
  margin: 10px 0;
}
</style>
