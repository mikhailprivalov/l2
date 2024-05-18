<template>
  <div>
    <div class="main">
      <div class="billing-info">
        <div class="billing-info-col billing-info-row">
          <RadioField
            v-model="selectedType"
            :variants="typesCompany"
            @modified="changeType"
          />
        </div>
      </div>
      <div class="billing-info">
        <div class="billing-info-col">
          <div class="billing-info-row">
            <div class="input-group">
              <span
                class="input-group-addon nbr"
                style="width: 150px"
              >Контрагент</span>
              <Treeselect
                v-model="selectedCompany"
                :options="companies"
                :normalizer="normalizer"
                placeholder="Выберите компанию..."
              />
            </div>
          </div>
          <div
            v-if="selectedCompany"
            class="billing-info-row"
          >
            <div class="input-group">
              <span
                class="input-group-addon nbr"
                style="width: 150px"
              >Счета</span>
              <Treeselect
                v-model="selectedBilling"
                :options="billings"
                placeholder="Выберите счёт..."
              />
            </div>
          </div>
          <div
            v-if="selectedCompany"
            class="billing-info-row flex"
          >
            <div class="date-block">
              <input
                v-model="currentBillingData.dateStart"
                class="form-control"
                type="date"
              >
              <div style="padding-top: 5px;">
                -
              </div>
              <input
                v-model="currentBillingData.dateEnd"
                class="form-control"
                type="date"
              >
            </div>
            <div
              v-if="selectedCompany"
            >
              <Treeselect
                v-model="selectedPrice"
                :options="prices"
                placeholder="Выберите прайс..."
              />
            </div>
          </div>
          <div class="billing-info-row">
            <button
              v-if="selectedBilling && selectedPrice && !currentBillingData.isConfirmed"
              class="btn btn-blue-nb"
              @click="updateBilling"
            >
              Сохранить проект
            </button>
            <button
              v-if="selectedPrice && !selectedBilling"
              class="btn btn-blue-nb"
              @click="createBilling"
            >
              Новый счет
            </button>
            <button
              v-if="selectedBilling && selectedPrice && !currentBillingData.isConfirmed"
              class="btn btn-blue-nb"
              @click="confirmBilling"
            >
              Записать счет
            </button>
            <button
              v-if="currentBillingData.isConfirmed"
              class="btn btn-blue-nb"
              @click="cancelBilling"
            >
              Сбросить счет
            </button>
            <button
              v-if="selectedBilling && selectedPrice && currentBillingData.isConfirmed"
              class="btn btn-blue-nb"
              @click="downloadBillingExcel"
            >
              <i class="fa-solid fa-download" />
              Excel
            </button>
          </div>
        </div>
        <div
          v-if="selectedCompany"
          class="billing-info-col"
        >
          <div class="input-group billing-info-row">
            <span
              class="input-group-addon nbr"
              style="width: 150px"
            >От</span>
            <input
              v-model="currentBillingData.dateFrom"
              class="form-control input-36"
              type="date"
            >
          </div>
          <div class="input-group billing-info-row">
            <span
              class="input-group-addon nbr"
              style="width: 150px"
            >Реестр №</span>
            <input
              v-model="currentBillingData.registryNumber"
              class="form-control input-36"
            >
          </div>
          <div class="input-group billing-info-row">
            <span
              class="input-group-addon nbr"
              style="width: 150px"
            >Договор №</span>
            <input
              :disabled="true"
              :value="currentContractNumber"
              class="form-control input-36"
            >
          </div>
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
  dateFrom: '',
  registryNumber: '',
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
  dateFrom: '',
  registryNumber: '',
});

const datesFilled = computed(() => !!(currentBillingData.value.dateStart && currentBillingData.value.dateEnd));
const clearBilling = () => {
  currentBillingData.value = { ...billingTemplate.value };
};

const prices = ref([]);
const selectedPrice = ref(null);
const getPrices = async () => {
  await store.dispatch(actions.INC_LOADING);
  const billingData = { ...currentBillingData.value, typeCompany: selectedType.value, hospitalId: selectedCompany.value };
  const { data } = await api('contracts/get-hospital-prices', { ...billingData });
  await store.dispatch(actions.DEC_LOADING);
  prices.value = data;
};

const getBilling = async () => {
  await store.dispatch(actions.INC_LOADING);
  const {
    ok, result, message, columns, tableData,
  } = await api('contracts/get-billing', {
    billingId: selectedBilling.value,
    typeCompany: selectedType.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    currentBillingData.value = result;
    colTable.value = columns;
    services.value = tableData;
    selectedPrice.value = result.priceId;
  } else {
    root.$emit('msg', 'error', message);
  }
};

watch(selectedBilling, () => {
  if (selectedBilling.value) {
    getBilling();
  } else {
    clearBilling();
  }
});

const updateBilling = async () => {
  if (selectedBilling.value && (currentBillingData.value.registryNumber && currentBillingData.value.dateFrom)) {
    const billingData = { ...currentBillingData.value, typeCompany: selectedType.value };
    const apiPoint = 'contracts/update-billing';
    const priceId = selectedPrice.value;
    await store.dispatch(actions.INC_LOADING);
    const {
      ok, billingInfo, columns, tableData,
    } = await api(apiPoint, { ...billingData, priceId });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      await getBillings();
      colTable.value = columns;
      services.value = tableData;
      root.$emit('msg', 'ok', `${billingInfo} сохранен`);
    } else {
      root.$emit('msg', 'error', 'ошибка');
    }
  } else {
    root.$emit('msg', 'error', 'От или реестр № не заполнены');
  }
};

const confirmBilling = async () => {
  if (selectedBilling.value) {
    const billingData = { ...currentBillingData.value, typeCompany: selectedType.value };
    const apiPoint = 'contracts/confirm-billing';
    const priceId = selectedPrice.value;
    await store.dispatch(actions.INC_LOADING);
    const {
      ok, billingInfo,
    } = await api(apiPoint, { ...billingData, priceId });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      await getBilling();
      root.$emit('msg', 'ok', 'Счёт подтверждён');
    } else {
      root.$emit('msg', 'error', 'ошибка');
    }
  }
};

const cancelBilling = async () => {
  if (selectedBilling.value) {
    const apiPoint = 'contracts/cancel-billing';
    await store.dispatch(actions.INC_LOADING);
    const {
      ok, billingInfo,
    } = await api(apiPoint, { id: selectedBilling.value });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      await getBilling();
      root.$emit('msg', 'ok', `${billingInfo} Отменен`);
    } else {
      root.$emit('msg', 'error', 'ошибка');
    }
  }
};

const createBilling = async () => {
  if (!currentBillingData.value.registryNumber || !currentBillingData.value.dateFrom) {
    root.$emit('msg', 'error', 'От или реестр № не заполнены');
  } else {
    const hospitalId = selectedType.value !== 'Работодатель' ? selectedCompany.value : null;
    const companyId = selectedType.value === 'Работодатель' ? selectedCompany.value : null;
    const priceId = selectedPrice.value;
    const billingData = {
      ...currentBillingData.value,
      hospitalId,
      companyId,
      priceId,
      typeCompany: selectedType.value,
    };
    const apiPoint = 'contracts/create-billing';
    await store.dispatch(actions.INC_LOADING);
    const { ok, billingInfo } = await api(apiPoint, { ...billingData });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      root.$emit('msg', 'ok', 'Создано');
      await getBillings();
      selectedBilling.value = billingInfo;
    } else {
      root.$emit('msg', 'error', 'ошибка');
    }
  }
};

watch(() => [currentBillingData.value.dateStart, currentBillingData.value.dateEnd], () => {
  if (datesFilled.value) {
    getPrices();
  }
});

watch(selectedCompany, () => {
  if (selectedCompany.value) {
    selectedBilling.value = null;
    getBillings();
  } else {
    selectedBilling.value = null;
  }
});

const currentContractNumber = ref('');
watch(selectedPrice, () => {
  if (selectedPrice.value) {
    const currentPrice = prices.value.find((price) => price.id === selectedPrice.value);
    if (currentPrice) {
      currentContractNumber.value = currentPrice.contractNumber;
    } else {
      currentContractNumber.value = '';
    }
  } else {
    currentContractNumber.value = '';
  }
});

const downloadBillingExcel = async () => {
  window.open(`/forms/xlsx?type=101.01&billingId=${selectedBilling.value}`, '_blank');
};

</script>

<style scoped lang="scss">
.main {
  margin: 0 20px;
}
.billing-info {
  display: grid;
  grid-template-columns: minmax(400px, 1fr) minmax(100px, 0.5fr) minmax(0, 0.5fr);
  grid-column-gap: 5px;
  justify-items: center;
}
.billing-info-col {
  width: 100%;
}
.billing-info-row {
  width: 100%;
  margin: 10px 0;
}
.billing-info-row:nth-child(1) {
  margin: 0 0 10px 0
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
.input-36 {
  height: 36px;
}
</style>
