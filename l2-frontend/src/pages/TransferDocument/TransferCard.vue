<template>
  <div>
    <div class="radio-button-object">
      <RadioField
        v-model="searchTypesObject"
        :variants="typesObject"
        full-width
        @modified="filteredGroupObject"
      />
    </div>
    <div
      class="row"
      style="padding-top:35px;"
    >
      <div class="col-xs-5">
        <div class="input-group treeselect-noborder-left">
          <span class="input-group-addon">Откуда</span>
          <Treeselect
            v-model="source"
            :multiple="false"
            :disable-branch-nodes="true"
            :flatten-search-results="true"
            :options="sources"
            :clearable="true"
            class="treeselect-wide"
            placeholder="Кабинет не указаны"
          />
        </div>
      </div>
      <div class="col-xs-5">
        <div class="input-group treeselect-noborder-left">
          <span class="input-group-addon">Куда</span>
          <Treeselect
            v-model="destination"
            :multiple="false"
            :disable-branch-nodes="true"
            :flatten-search-results="true"
            :options="destinations"
            placeholder="Кабинет не указаны"
            :clearable="false"
            class="treeselect-wide"
          />
        </div>
      </div>
      <div class="col-xs-2">
        <button
          class="btn last btn-blue-nb nbr"
          title="Выполнить"
          @click="executeTranfer"
        >
          Выполнить
        </button>
      </div>
    </div>
    <div
      class="margin-bottom"
    >
      <input
        v-model.trim="search"
        class="form-control search"
        placeholder="Поиск по номеру"
      >
    </div>
    <div
      class="card-no-hover card card-1"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col width="100">
            <col>
            <col width="28">
          </colgroup>
          <thead class="sticky">
            <tr>
              <th class="text-center">
                № карты
              </th>
              <th class="text-center">
                ФИО
              </th>
              <th class="nopd noel">
                <input
                  v-model="allChecked"
                  type="checkbox"
                >
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in transferCards"
              :key="row.pk"
            >
              <td class="text-center">
                {{ row.number_p }}
              </td>
              <td class="text-center">
                {{ row.fio }}
              </td>
              <td class="nopd">
                <input
                  v-model="row.checked"
                  type="checkbox"
                >
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, onBeforeMount, onMounted, ref, watch,
} from 'vue';
import Component from 'vue-class-component';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import RadioField from '@/fields/RadioField.vue';

const typesObject = ref(['Принять', 'Отправить']);
const searchTypesObject = ref('');
const destination = ref(-1);
const source = ref(-1);
const allChecked = ref(false);
const checked = ref([]);
const search = ref('');

const destinations = ref([
  { id: -1, label: 'не выбрано' },
  { id: 1, label: 'каб1' }, { id: 2, label: 'каб2' }, { id: 3, label: 'каб3' }]);
const sources = ref([
  { id: -1, label: 'не выбрано' },
  { id: 1, label: 'каб11' }, { id: 2, label: 'каб22' }, { id: 3, label: 'каб33' }]);

const transferCards = [
  {
    pk: 1, number_p: 11, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 2, number_p: 22, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 3, number_p: 33, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 1, number_p: 11, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 2, number_p: 22, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 3, number_p: 33, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 1, number_p: 11, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 2, number_p: 22, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 3, number_p: 33, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 1, number_p: 11, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 1, number_p: 11, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 2, number_p: 22, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 3, number_p: 33, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 1, number_p: 11, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 2, number_p: 22, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 3, number_p: 33, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 1, number_p: 11, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 2, number_p: 22, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 3, number_p: 33, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 1, number_p: 11, fio: 'Ивано Иван Иванович', checked: false,
  },

];

function filteredGroupObject() {
  console.log(searchTypesObject);
}

function executeTranfer() {
  console.log('Выполнить');
}

watch(allChecked, () => {
  for (const row of transferCards) {
    row.checked = allChecked.value;
  }
});

watch(transferCards, () => {
  checked.value = [];
  for (const row of transferCards) {
    if (row.checked) {
      checked.value.push(row.pk);
    }
  }
});

</script>

<style scoped>
.radio-button-object {
  width: 70%;
  margin-left: auto;
  margin-right: auto;
  margin-top: 2%;
}

.scroll {
  min-height: 106px;
  max-height: calc(100vh - 250px);
  overflow-y: auto;
}

::v-deep .form-control {
  border: none;
  padding: 6px 6px;
  background-color: transparent;
}
::v-deep .card {
  margin: 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.margin-bottom {
  margin-bottom: 20px;
}

.sticky {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: white;
}
</style>
