<template>
  <div :class="$style.tableRoot">
    <Spinner v-if="!hasFirstLoading" />
    <template v-else>
      <button
        class="btn btn-primary-nb btn-blue-nb nbr"
        type="button"
        @click="addRecord"
      >
        <i class="fa fa-plus" /> Создать запись
      </button>
      <VeTable
        ref="table"
        :columns="columns"
        :table-data="data.result.rows"
        :cell-style-option="cellStyleOption"
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
  computed, onMounted, onUnmounted, ref, watch,
} from 'vue';
import {
  VeLoading,
  VeLocale,
  VePagination,
  VeTable,
} from 'vue-easytable';
import 'vue-easytable/libs/theme-default/index.css';

import Spinner from '@/components/Spinner.vue';
import useApi, { ApiStatus } from '@/api/useApi';
import ruRu from '@/locales/ve';
import { EDIT_OPEN, EDIT_SAVED_OBJECT } from '@/store/action-types';
import { useStore } from '@/store';

import { ListElement } from './EditableList.vue';

VeLocale.use(ruRu);

const store = useStore();

let loadingInstance: VeLoading | null = null;

const props = defineProps<{
  formType: string,
  filters?: Record<string, any>,
}>();

const pageSize = ref(100);
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
  call,
} = useApi<ApiType>(apiParams, { defaultData });

const pageNumberChange = (number: number) => {
  page.value = number;
};

const pageSizeChange = (size: number) => {
  pageSize.value = size;
};

const table = ref<any>(null);

watch(table, () => {
  if (table.value?.$el) {
    if (loadingInstance) {
      loadingInstance.destroy();
    }
    loadingInstance = VeLoading({
      target: table.value?.$el,
      name: 'wave',
      tip: 'загрузка...',
    });
  }
});

watch(status, () => {
  if (status.value === ApiStatus.SUCCESS && !hasFirstLoading.value) {
    hasFirstLoading.value = true;
  } else if (loadingInstance) {
    if (status.value === ApiStatus.SUCCESS) {
      loadingInstance.close();
    } else {
      loadingInstance.show();
    }
  }
});

const columns = computed(() => data.value?.viewParams?.tableColumns?.map((cell: any) => (cell.key === 'edit' ? {
  key: 'edit',
  field: '',
  title: 'Редактировать',
  align: 'center',
  disableResizing: true,
  width: 100,
  renderBodyCell: ({ row: r }, h) => h('button', {
    class: 'btn btn-primary-nb btn-blue-nb nbr',
    on: {
      click: (e: any) => {
        e.stopPropagation();
        store.dispatch(EDIT_OPEN, { editId: r.id, formType: props.formType, filters: props.filters });
      },
    },
  }, [h('i', { class: 'fa fa-pencil' })]),
} : cell)));

const cellStyleOption = {
  bodyCellClass: ({ column }) => {
    if (column.key === 'edit') {
      return 'edit-cell';
    }

    return '';
  },
};

onMounted(() => {
  store.subscribeAction(action => {
    if (
      action.type === EDIT_SAVED_OBJECT
      && (
        action.payload?.formType === props.formType
        || store.getters.editStackHasFormType(props.formType)
      )
      && action.payload?.result
    ) {
      call();
    }
  });
});

onUnmounted(() => {
  if (loadingInstance) {
    loadingInstance.destroy();
  }
});

const addRecord = () => {
  store.dispatch(EDIT_OPEN, { editId: null, formType: props.formType, filters: props.filters });
};
</script>

<style lang="scss">
.edit-cell {
  padding: 0 !important;
}
</style>

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
