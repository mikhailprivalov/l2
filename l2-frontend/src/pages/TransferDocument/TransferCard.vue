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
      style="padding-top:25px;"
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
            :clearable="false"
            class="treeselect-wide"
          />
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-xs-5">
        <div
          class="input-group"
          style="padding-top: 20px"
        >
          <span class="input-group-addon">Номер карты</span>
          <input
            v-model="search"
            type="text"
            size="40"
            class="form-control form-control-forced-last"
            data-container="body"
            data-toggle="popover"
            data-placement="bottom"
            data-content=""
            spellcheck="false"
            autofocus
            placeholder="Введите номер карты"
            @keyup.enter="load"
          >
          <span class="input-group-btn">
            <button
              class="btn btn-blue-nb"
              type="button"
              @click="executeTranfer"
            >Загрузить</button>
          </span>
        </div>
      </div>
      <div
        class="col-xs-5"
        style="padding-top: 20px; padding-left: 250px"
      >
        <button
          class="btn last btn-blue-nb nbr"
          title="Выполнить"
          @click="executeTranfer"
        >
          {{ searchTypesObject }} карты:  <strong> {{ currentCount }} шт</strong>
        </button>
      </div>
    </div>
    <div
      class="scroll"
      style="padding-top: 10px"
    >
      <table class="table table-bordered">
        <colgroup>
          <col width="300">
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
                v-model="checkedCards"
                type="checkbox"
                :value="row"
              >
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import RadioField from '@/fields/RadioField.vue';
import api from '@/api';

const typesObject = ref(['Принять', 'Отправить']);
const searchTypesObject = ref('');
const destination = ref(-1);
const source = ref(-1);
const allChecked = ref(false);
const checkedCards = ref([]);
const search = ref('');
const destinations = ref([]);
const sources = ref([]);

const transferCards = ref([
  {
    pk: 1, number_p: 11, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 2, number_p: 22, fio: 'Ивано Иван Иванович', checked: false,
  },
  {
    pk: 3, number_p: 33, fio: 'Ивано Иван Иванович', checked: false,
  },
]);

function filteredGroupObject() {
  console.log(searchTypesObject);
}

function executeTranfer() {
  console.log('Выполнить');
  console.log(checkedCards);
}

watch(allChecked, () => {
  if (allChecked.value) {
    checkedCards.value = [];
    for (const row of transferCards.value) {
      checkedCards.value.push(row);
    }
  } else checkedCards.value = [];
});

async function getDestinationsSources() {
  const data = await api('transfer-document/get-destination-source', searchTypesObject);
  source.value = -1;
  destination.value = -1;
  sources.value = data.sources;
  destinations.value = data.destinations;
}

watch(searchTypesObject, () => {
  getDestinationsSources();
});

const currentCount = computed(() => checkedCards.value.length);

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

.table {
  margin-bottom: 0;
  table-layout: fixed;
}

.sticky {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: white;
}

input[type=text]:focus {
  background-color: #e1f2fe;
}

input[type=text] {
  background-color: #FFFFFF;
}
</style>
