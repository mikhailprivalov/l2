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
          <label>Компании</label>
          <Treeselect
            v-model="selectedCompany"
            :options="companies"
            :normalizer="normalizer"
            placeholder="Выберите компанию..."
          />
        </div>
        <div
          v-if="selectedCompany"
          class="margin-item"
        >
          <label>Счета</label>
          <Treeselect
            v-model="selectedBilling"
            :options="billings"
            placeholder="Выберите счёт..."
          />
        </div>
        <div
          v-if="selectedCompany"
          class="margin-item flex"
        >
          <div class="date-block">
            <label>c</label>
            <input
              v-model="currentBilling.dateStart"
              class="form-control"
              type="date"
            >
            <label>по</label>
            <input
              v-model="currentBilling.dateEnd"
              class="form-control"
              type="date"
            >
          </div>
          <button
            class="btn btn-blue-nb"
            @click="updateBilling"
          >
            {{ selectedBilling ? 'Сохранить' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref, watch } from 'vue';
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

const billings = ref([]);
const selectedBilling = ref(null);
const getBillings = async () => {
  const id = selectedType.value === 'Работодатель' ? { companyId: selectedCompany.value } : { hospitalId: selectedCompany.value };
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('contracts/get-billings', id);
  await store.dispatch(actions.DEC_LOADING);
  billings.value = result;
};

watch(selectedCompany, () => {
  if (selectedCompany.value) {
    selectedBilling.value = null;
    getBillings();
  }
});

const billingTemplate = ref({
  billingId: -1,
  hospitalId: -1,
  companyId: -1,
  createAt: '',
  whoCreat: '',
  dateStart: '',
  dateEnd: '',
  info: '',
  isConfirmed: '',
});

const currentBillingData = ref({
  billingId: -1,
  hospitalId: -1,
  companyId: -1,
  createAt: '',
  whoCreat: '',
  dateStart: '',
  dateEnd: '',
  info: '',
  isConfirmed: '',
});

const getBilling = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('contracts/get-billing', { billingId: selectedBilling.value });
  await store.dispatch(actions.DEC_LOADING);
  currentBillingData.value = result;
};
const clearBilling = () => {
  currentBillingData.value = { ...billingTemplate.value };
};

watch(selectedBilling, () => {
  if (selectedBilling.value) {
    getBilling();
  } else {
    clearBilling();
  }
});

const updateBilling = async () => {
  const hospitalId = selectedType.value !== 'Работодатель' ? selectedCompany.value : -1;
  const companyId = selectedType.value === 'Работодатель' ? selectedCompany.value : -1;
  let billingData = {};
  if (currentBillingData.value) {
    billingData = { ...currentBillingData.value };
  } else {
    billingData = { ...currentBillingData.value, hospitalId, companyId };
  }
  await store.dispatch(actions.INC_LOADING);
  const { ok, billingInfo } = await api('contracts/update-billing', { ...billingData });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Сохранено');
    console.log(billingInfo);
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
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
.flex {
  display: flex;
  gap: 10px;
}
.date-block {
  display: flex;
  gap: 10px;
  position: relative;
  width: 70%;
}
</style>
