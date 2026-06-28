<template>
  <div
    ref="root"
    class="district-root"
  >
    <div class="district-sidebar">
      <div
        v-for="row in data"
        :key="row.pk"
        class="sidebar-btn-wrapper"
      >
        <button
          class="btn btn-blue-nb sidebar-btn"
          @click="editDistrict(row)"
        >
          {{ row.title }}
        </button>
      </div>
      <div
        class="
        side-bottom"
      >
        <div
          class="input-group width-side"
        >
          <input
            v-model="newDistrictTitle"
            type="text"
            class="form-control"
            autofocus
            placeholder="Название участка"
          >
          <span class="input-group-btn">
            <button
              class="btn last btn-blue-nb nbr margin-right-btn"
              type="button"
              @click="addNewDistrict"
            >Добавить</button>
          </span>
        </div>
      </div>
    </div>
    <div class="district-content">
      <div>
        <h5 class="text-align-center">
          {{ district.title }}
        </h5>
        <div
          v-if="district.title"
          class="district-limit-research"
        >
          <table class="table table-bordered">
            <caption>Ограничения назначения услуг</caption>
            <colgroup>
              <col>
              <col width="150">
              <col width="140">
              <col width="30">
            </colgroup>
            <thead>
              <tr>
                <th>Наименование</th>
                <th>Лимит </th>
                <th>Период</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(val, index) in tbData"
                :key="index"
              >
                <td class="cl-td">
                  <Treeselect
                    v-model="val.current_researches"
                    class="treeselect-noborder"
                    :multiple="false"
                    :options="researches"
                    placeholder="Не выбран"
                    :align="left"
                  />
                </td>
                <td class="cl-td">
                  <div class="input-group">
                    <input
                      v-model="val.count"
                      type="number"
                      class="form-control border-none"
                      placeholder="Кол-во в месяц"
                    >
                  </div>
                </td>
                <td class="cl-td">
                  <select
                    v-model="val.type"
                    class="form-control border-none"
                  >
                    <option
                      v-for="t in types"
                      :key="t"
                      :value="t"
                    >
                      {{ t }}
                    </option>
                  </select>
                </td>
                <td class="text-center cl-td">
                  <button
                    v-tippy="{ placement: 'bottom' }"
                    class="btn btn-blue-nb"
                    title="Удалить строку"
                    @click="deleteRow(index)"
                  >
                    <i class="fa fa-times" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div class="row">
            <div class="col-xs-8" />
            <div class="col-xs-4">
              <button
                class="btn btn-blue-nb add-row"
                @click="saveLimitData(tbData)"
              >
                Сохранить
              </button>
              <button
                class="btn btn-blue-nb add-row"
                @click="addNewRow"
              >
                Добавить ограничение
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import {
  getCurrentInstance, onMounted, ref, watch,
} from 'vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import api from '@/api';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';

const types = ['День', 'Месяц'];
const makeDefaultRow = (type = null) => ({ count: 0, type: type || types[0] });

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const emit = defineEmits(['modified']);

const tbData = ref<any[]>([makeDefaultRow()]);
const data = ref<any[]>([]);
const researches = ref<any[]>([]);
const district = ref<any>({});
const newDistrictTitle = ref('');

const changeValue = (newVal: any[]) => {
  emit('modified', newVal);
};

const loadDistrict = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('districts/districts-load');
  data.value = result;
  await store.dispatch(actions.DEC_LOADING);
};

watch(
  tbData,
  () => {
    changeValue(tbData.value);
  },
  { immediate: true, deep: true },
);

const saveLimitData = async (rows: any[]) => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('districts/district-save-limit', {
    district: district.value.pk,
    tb_data: rows,
  });
  if (ok) {
    root.$emit('msg', 'ok', message);
  } else {
    root.$emit('msg', 'error', message);
  }
  await store.dispatch(actions.DEC_LOADING);
};

const addNewRow = () => {
  const tl = tbData.value.length;
  tbData.value.push(makeDefaultRow(tl > 0 ? tbData.value[tl - 1].type : null));
};

const addNewDistrict = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('districts/district-create', {
    district: newDistrictTitle.value,
  });
  if (ok) {
    root.$emit('msg', 'ok', message);
  } else {
    root.$emit('msg', 'error', message);
  }
  await loadDistrict();
  newDistrictTitle.value = '';
  await store.dispatch(actions.DEC_LOADING);
};

const deleteRow = (index: number) => {
  tbData.value.splice(index, 1);
};

const editDistrict = async (row: any) => {
  await store.dispatch(actions.INC_LOADING);
  district.value = row;
  const { result } = await api('districts/district-edit', { pk: row.pk });
  tbData.value = result;
  await store.dispatch(actions.DEC_LOADING);
};

onMounted(() => {
  api('researches/research-dispensary').then((rows) => {
    researches.value = rows;
  });
  loadDistrict();
});
</script>

<style scoped lang="scss">
.district-root {
  position: absolute;
  top: 36px;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: stretch;
  flex-direction: row;
  flex-wrap: nowrap;
  align-content: stretch;
  overflow-x: hidden;

  & > div {
    align-self: stretch;
  }
}

.district-sidebar {
  width: 280px;
  border-right: 1px solid #b1b1b1;
  display: flex;
  flex-direction: column;
}

.district-content {
  display: flex;
  flex-direction: column;
  width: calc(100% - 280px);
}

.district-limit-research {
  width: calc(100% - 250px);
  display: flex;
  flex-direction: column;
  margin-left: 125px;
}

.side-bottom {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    border-radius: 0;
    display: flex;
    flex-direction: row;

    .btn {
      height: 34px;
      border-radius: 0;
    }
    .width-side {
      width: 280px;
    }
  }

.sidebar-btn {
  border-radius: 0;

  &:not(.text-center) {
    text-align: left;
  }

  border-top: none !important;
  border-right: none !important;
  border-left: none !important;
  padding: 0 12px;
  height: 28px;

  &:not(:hover):not(.colorBad),
  &.active-btn:hover:not(.colorBad) {
    cursor: default;
    background-color: rgba(#000, 0.02) !important;
    color: #000;
    border-bottom: 1px solid #b1b1b1 !important;
  }
}

.sidebar-btn-wrapper {
  display: flex;
  flex-direction: row;

  .sidebar-btn:first-child {
    flex: 1 1 auto;
  }
}

.add-row {
  float: right;
  margin-left: 10px;
}

.cl-td ::v-deep {
  label {
    justify-content: left;
  }
}

.border-none {
  border: none;
}

.text-align-center {
  text-align: center;
}

.margin-right-btn {
  margin-right: -1px;
}

</style>
