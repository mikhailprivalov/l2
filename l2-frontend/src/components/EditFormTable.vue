<template>
  <div :class="$style.tableRoot">
    <Spinner v-if="!hasFirstLoading" />
    <template v-else>
      <VeTable
        :columns="data.viewParams.tableColumns"
        :table-data="data.result.rows"
        border-y
        row-key-field-name="id"
      />
      <div
        v-show="data.result.totalCount === 0"
        :class="$style.empty"
      >
        нет записей
      </div>
      <div :class="$style.tablePagination">
        <VePagination
          :total="data.result.totalCount"
          :page-index="page"
          :page-size="pageSize"
          :page-size-option="pageSizeOption"
          @on-page-number-change="pageNumberChange"
          @on-page-size-change="pageSizeChange"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import {
  computed, ref, watch, onMounted, onBeforeUnmount,
} from 'vue';
import {
  VeLocale, VePagination, VeTable,
} from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';

import Spinner from '@/components/Spinner.vue';
import useApi, { ApiStatus } from '@/api/useApi';
import ruRu from '@/locales/ve';

import { ListElement } from './EditableList.vue';

VeLocale.use(ruRu);

let loadingInstance: any = null;
let loadingId = '';

veLoading({
    target: "#loading-1",
    name: "grid",
    tip: "loading...",
});

const props = defineProps<{
  formType: string,
  filters?: Record<string, any>,
}>();

const pageSize = ref(30);
const page = ref(1);
const hasFirstLoading = ref(false);
const pageSizeOption = ref([30, 50, 100, 300]);

const apiParams = computed(() => ({
  path: 'edit-forms/objects/search',
  data: {
    formType: props.formType,
    filters: props.filters,
    page: page.value,
    perPage: pageSize.value,
  },
}));

interface ApiType {
  result: {
    page: number,
    pages: number,
    perPage: number,
    totalCount: number,
    rows: ListElement[],
  },
  viewParams: {
    tableColumns: any[],
  },
}

const defaultData = (): ApiType => ({
  result: {
    page: 1,
    pages: 1,
    perPage: pageSize.value,
    totalCount: 0,
    rows: [],
  },
  viewParams: {
    tableColumns: [],
  },
});

const {
  data,
  status,
} = useApi<ApiType>(apiParams, { defaultData });

const pageNumberChange = (number: number) => {
  page.value = number;
};

const pageSizeChange = (size: number) => {
  pageSize.value = size;
};

watch(status, () => {
  if (status.value === ApiStatus.SUCCESS && !hasFirstLoading.value) {
    hasFirstLoading.value = true;
  }
});
</script>

<style lang="scss" module>
.tableRoot {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: #fff;
}

.tablePagination {
  margin-top: 20px;
  text-align: right;
}

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  width: 100%;
  color: #666;
  font-size: 16px;
  border: 1px solid #eee;
  border-top: 0;
}
</style>
