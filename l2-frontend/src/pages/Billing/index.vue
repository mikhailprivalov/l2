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
              v-model="currentBillingData.dateStart"
              class="form-control"
              type="date"
            >
            <label>по</label>
            <input
              v-model="currentBillingData.dateEnd"
              class="form-control"
              type="date"
            >
          </div>
          <button
            class="btn btn-blue-nb"
            @click="selectedBilling ? updateBilling : createBilling"
          >
            {{ selectedBilling ? 'Сохранить' : 'Создать' }}
          </button>
        </div>
      </div>
      <div>
        <VeTable
          :columns="columns"
          :table-data="servicePagination"
          row-key-field-name="card_id"
        />
        <div
          v-show="servicePagination.length === 0"
          class="empty-list"
        >
          Нет записей
        </div>
        <div class="flex flex-space-between">
          <VePagination
            :total="services.length"
            :page-index="page"
            :page-size="pageSize"
            :page-size-option="pageSizeOptions"
            @on-page-number-change="pageNumberChange"
            @on-page-size-change="pageSizeChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, ref, watch,
} from 'vue';
import {
  VeLocale,
  VePagination,
  VeTable,
} from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import RadioField from '@/fields/RadioField.vue';
import * as actions from '@/store/action-types';
import api from '@/api';
import { useStore } from '@/store';
import ruRu from '@/locales/ve';

VeLocale.use(ruRu);

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
  } else {
    selectedBilling.value = null;
  }
});

const billingTemplate = ref({
  id: -1,
  hospitalId: null,
  companyId: null,
  createAt: '',
  whoCreat: '',
  dateStart: '',
  dateEnd: '',
  info: '',
  isConfirmed: '',
});

const currentBillingData = ref({
  id: -1,
  hospitalId: null,
  companyId: null,
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
  const billingData = { ...currentBillingData.value, typeCompany: selectedType.value };
  await store.dispatch(actions.INC_LOADING);
  const { ok, billingId, result, iss, priceIk } = await api('contracts/update-billing', { ...billingData });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Сохранено');
    await getBillings();
    console.log(billingId);
    console.log(result);
    console.log(iss);
    console.log(priceIk);
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

const createBilling = async () => {
  const hospitalId = selectedType.value !== 'Работодатель' ? selectedCompany.value : null;
  const companyId = selectedType.value === 'Работодатель' ? selectedCompany.value : null;
  const billingData = {
    ...currentBillingData.value, hospitalId, companyId, typeCompany: selectedType.value,
  };
  await store.dispatch(actions.INC_LOADING);
  const {
    ok, billingInfo, result, iss, priceIk,
  } = await api('contracts/create-billing', { ...billingData });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Сохранено');
    await getBillings();
    selectedBilling.value = billingInfo;
    console.log(result);
    console.log(iss);
    console.log(priceIk);
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

const page = ref(1);
const pageSize = ref(25);
const pageSizeOptions = ref([25, 50, 100]);
const pageNumberChange = (number: number) => {
  page.value = number;
};
const pageSizeChange = (size: number) => {
  pageSize.value = size;
};

const columns = ref([
  {
    field: 'research_title',
    key: 'research_title',
    title: 'Услуга',
  },
  {
    field: 'patient_fio',
    key: 'patient_fio',
    title: 'ФИО пациента',
  },
  {
    field: 'patient_born',
    key: 'patient_born',
    title: 'Д.Р. Пациента',
  },
  {
    field: 'tube_number',
    key: 'tube_number',
    title: '№ пробирки',
  },
  {
    field: 'coast',
    key: 'coast',
    title: 'Цена',
  },
]);

const services = ref([]);
const servicePagination = computed(() => services.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value));

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
.empty-list {
  width: 85px;
  margin: 20px auto;
}
</style>
