<template>
  <div class="main">
    <div class="filters">
      <div>
        <div class="filter-item">
          <label>Организации</label>
          <Treeselect
            v-model="filters.organizationId"
            :options="organizations"
            :clearable="false"
            class="treeselect-34px"
            placeholder="Выберите организацию"
            :append-to-body="true"
            :limit="1"
            :limit-text="count => `и ещё ${count}`"
          />
        </div>
      </div>
      <div>
        <div class="filter-item">
          <label>Подразделения</label>
          <Treeselect
            v-model="filters.departementIds"
            :options="refBooks.departments"
            :clearable="false"
            :multiple="true"
            class="treeselect-34px"
            placeholder="Выберите подразделения"
            :append-to-body="true"
            :limit="1"
            :limit-text="count => `и ещё ${count}`"
          />
        </div>
      </div>
      <div>
        <div class="filter-item">
          <label>Должности</label>
          <Treeselect
            v-model="filters.positionsIds"
            :options="refBooks.positions"
            :clearable="false"
            :multiple="true"
            class="treeselect-34px"
            placeholder="Выберите должности"
            :append-to-body="true"
            :limit="1"
            :limit-text="count => `и ещё ${count}`"
          />
        </div>
      </div>
      <div>
        <div class="filter-item">
          <label>Вид занятости</label>
          <Treeselect
            v-model="filters.employmentFormIds"
            :options="refBooks.employmentForms"
            :clearable="false"
            :multiple="true"
            class="treeselect-34px"
            placeholder="Выберите форму занятости"
            :append-to-body="true"
            :limit="1"
            :limit-text="count => `и ещё ${count}`"
          />
        </div>
      </div>
    </div>
    <div class="search">
      <label>Поиск</label>
      <input
        v-model.trim="search"
        class="form-control"
        placeholder="Введите значение"
      >
    </div>
    <div class="employees">
      <VeTable
        :columns="columns"
        :table-data="employeesPagination"
        max-height="calc(100vh - 241px)"
      />
      <div
        v-show="employeesPagination.length === 0"
        class="empty-list"
      >
        Нет записей
      </div>
      <div class="flex flex-space-between">
        <VePagination
          :total="filteredEmployees.length"
          :page-index="page"
          :page-size="pageSize"
          :page-size-option="pageSizeOptions"
          @on-page-number-change="pageNumberChange"
          @on-page-size-change="pageSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import {
  VeLocale,
  VePagination,
  VeTable,
} from 'vue-easytable';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import 'vue-easytable/libs/theme-default/index.css';
import ruRu from '@/locales/ve';

VeLocale.use(ruRu);

interface employeeData {
  employeeId: number,
  employmentForm: string,
  snils: string,
  tabelNumber: string,
  employeeFio: string,
  department: string,
  position: string,
  rate: number,
  dateEmployment: string,
  dateDismissal: string,
}

const root = getCurrentInstance().proxy.$root;
const store = useStore();

const userOrganizationId = computed(() => store.getters.user_data.hospital);

const filters = ref({
  organizationId: null,
  departementIds: null,
  positionsIds: null,
  employmentFormIds: null,
});

const organizations = ref([]);
const getOrganization = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('employees/get-organizations');
  await store.dispatch(actions.DEC_LOADING);
  organizations.value = result;
};

onMounted(() => {
  getOrganization();
});

watch(organizations, () => {
  filters.value.organizationId = userOrganizationId.value;
});

const refBooks = ref({
  departments: [],
  positions: [],
  employmentForms: [],
});

const getRefBooks = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('employees/get-ref-books', { organizationId: filters.value.organizationId });
  await store.dispatch(actions.DEC_LOADING);
  refBooks.value = result;
};

watch(() => filters.value.organizationId, () => {
  getRefBooks();
});

const search = ref('');

const columns = ref([
  {
    key: 'employmentForm', field: 'employmentForm', title: 'Вид занятости', align: 'center', width: 150,
  },
  {
    key: 'snils', field: 'snils', title: 'СНИЛС', align: 'center', width: 150,
  },
  {
    key: 'tabelNumber', field: 'tabelNumber', title: 'Табельный №', align: 'center', width: 150,
  },
  {
    key: 'employeeFio', field: 'employeeFio', title: 'Работник', align: 'center',
  },
  {
    key: 'department', field: 'department', title: 'Подразделение', align: 'center', width: 230,
  },
  {
    key: 'position', field: 'position', title: 'Должность', align: 'center', width: 150,
  },
  {
    key: 'rate', field: 'rate', title: 'Кол-во ставок', align: 'center', width: 70,
  },
  {
    key: 'dateEmployment', field: 'dateEmployment', title: 'Дата приема', align: 'center', width: 120,
  },
  {
    key: 'dateDismissal', field: 'dateDismissal', title: 'Дата увольнения', align: 'center', width: 120,
  },
]);
const page = ref(1);
const pageSize = ref(25);
const pageSizeOptions = [25, 50, 100];
const pageNumberChange = (number: number) => {
  page.value = number;
};
const pageSizeChange = (size: number) => {
  pageSize.value = size;
  page.value = 1;
};

const employees = ref<employeeData[]>([]);

const getEmployees = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('employees/get-employees', {
    organizationId: filters.value.organizationId,
    departmentIds: filters.value.departementIds,
    positionIds: filters.value.positionsIds,
    employmentFormIds: filters.value.employmentFormIds,
  });
  await store.dispatch(actions.DEC_LOADING);
  employees.value = result;
};

watch(() => filters.value, () => {
  getEmployees();
}, { deep: true });

const filteredEmployees = computed(() => employees.value.filter(employee => {
  const fio = employee.employeeFio.toLowerCase();
  const searchTerm = search.value.toLowerCase();
  return fio.includes(searchTerm);
}));

const employeesPagination = computed(() => filteredEmployees.value.slice((page.value - 1)
  * pageSize.value, page.value * pageSize.value));
</script>

<style scoped lang="scss">
.main {
  margin: 10px;
}
.filters {
  display: grid;
  background-color: #fff;
  border-radius: 4px;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  padding: 10px 0;
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
  max-height: 185px;
  overflow-y: auto;
  margin-bottom: 10px;
}
.filter-item {
  margin: 0 5px;
}
.search {
  margin-bottom: 10px;
}
.employees {
  background-color: #fff;
}
.empty-list {
  width: 85px;
  margin: 20px auto;
}
</style>
