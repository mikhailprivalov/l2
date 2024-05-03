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
            @click="updateBilling"
          >
            {{ selectedBilling ? 'Сохранить' : 'Создать' }}
          </button>
        </div>
      </div>
      <div
        v-if="selectedBilling"
        class="white_bg"
      >
        <VeTable
          :columns="colTable"
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

const page = ref(1);
const pageSize = ref(25);
const pageSizeOptions = ref([25, 50, 100]);
const pageNumberChange = (number: number) => {
  page.value = number;
};
const pageSizeChange = (size: number) => {
  pageSize.value = size;
};

const colTable = ref([]);
const services = ref([]);
const servicePagination = computed(() => services.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value));

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
  const { result, columns, tableData } = await api('contracts/get-billing', {
    billingId: selectedBilling.value,
    typeCompany: selectedType.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  currentBillingData.value = result;
  colTable.value = columns;
  services.value = tableData;
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
  let billingData = {};
  let apiPoint = '';
  if (selectedBilling.value) {
    billingData = { ...currentBillingData.value, typeCompany: selectedType.value };
    apiPoint = 'contracts/update-billing';
    await store.dispatch(actions.INC_LOADING);
    const {
      ok, billingInfo, columns, tableData,
    } = await api(apiPoint, { ...billingData });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      await getBillings();
      colTable.value = columns;
      services.value = tableData;
      root.$emit('msg', 'ok', `${billingInfo} сохранен`);
    } else {
      root.$emit('msg', 'ok', 'ошибка');
    }
  } else {
    const hospitalId = selectedType.value !== 'Работодатель' ? selectedCompany.value : null;
    const companyId = selectedType.value === 'Работодатель' ? selectedCompany.value : null;
    billingData = {
      ...currentBillingData.value, hospitalId, companyId, typeCompany: selectedType.value,
    };
    apiPoint = 'contracts/create-billing';
    await store.dispatch(actions.INC_LOADING);
    const { ok, billingInfo } = await api(apiPoint, { ...billingData });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      root.$emit('msg', 'ok', 'Создано');
      selectedBilling.value = billingInfo;
    } else {
      root.$emit('msg', 'ok', 'ошибка');
    }
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
.empty-list {
  width: 85px;
  margin: 20px auto;
}
.white_bg {
  background: #FFF;
}
</style>
