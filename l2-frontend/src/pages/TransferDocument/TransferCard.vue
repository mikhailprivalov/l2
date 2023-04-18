<template>
  <div>
    <div class="radio-button-object">
      <RadioField
        v-model="searchTypesObject"
        :variants="typesObject"
        full-width
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
            ref="fieldCard"
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
              @click="load"
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
          <col width="200">
          <col>
          <col width="28">
        </colgroup>
        <thead class="sticky">
          <tr>
            <th class="text-center">
              № карты
            </th>
            <th class="text-center">
              Кабинет
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
            :key="row.id"
          >
            <td class="text-center">
              {{ row.number_p }}
            </td>
            <td class="text-center">
              {{ row.room }}
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
const destinations = ref([]);
const destination = ref(-1);
const sources = ref([]);
const source = ref(-1);
const allChecked = ref(false);
const checkedCards = ref([]);
const search = ref('');

const fieldCard = ref(null);
const transferCards = ref([]);
const isCardStorage = ref(false);

function focusFieldCard() {
  fieldCard.value.focus();
}

async function load() {
  let isFind = false;
  for (const card of transferCards.value) {
    if (card.number_p === search.value && !checkedCards.value.includes(card)) {
      checkedCards.value.push(card);
      isFind = true;
      break;
    }
  }

  if (!isFind && isCardStorage.value) {
    const data = await api('transfer-document/get-card-by-number', search);
    if (data.card.id) {
      if (!checkedCards.value.includes(data.card)) {
        checkedCards.value.push(data.card);
      }
      if (!transferCards.value.includes(data.card)) {
        transferCards.value.push(data.card);
      }
    }
  }
}

async function executeTranfer() {
  if (searchTypesObject.value === 'Отправить') {
    await api(
      'transfer-document/send-document',
      { cards: checkedCards.value, source: source.value, destination: destination.value },
    );
  } else {
    await api(
      'transfer-document/accept-document',
      { cards: checkedCards.value, source: source.value, destination: destination.value },
    );
  }
  transferCards.value = transferCards.value.filter(x => !checkedCards.value.includes(x));
  focusFieldCard();
}

async function getDestinationsSources() {
  const data = await api('transfer-document/get-destination-source', searchTypesObject);
  source.value = -1;
  destination.value = -1;
  sources.value = data.sources;
  destinations.value = data.destinations;
}

async function cardAccept() {
  const data = await api('transfer-document/get-card-accept', { roomOutId: source.value, roomInId: destination.value });
  transferCards.value = data.cardToAccept;
}

async function cardSend() {
  const data = await api('transfer-document/get-card-send', source);
  transferCards.value = data.cardToSend;
}

const currentCount = computed(() => checkedCards.value.length);

function getIsCardStorage() {
  for (const s of sources.value) {
    if (s.id === source.value && s.isCardStorage) {
      return true;
    }
  }
  return false;
}

watch(allChecked, () => {
  if (allChecked.value) {
    checkedCards.value = [];
    for (const row of transferCards.value) {
      checkedCards.value.push(row);
    }
  } else checkedCards.value = [];
});

watch(searchTypesObject, () => {
  transferCards.value = [];
  checkedCards.value = [];
  getDestinationsSources();
});

watch([source, destination], () => {
  transferCards.value = [];
  checkedCards.value = [];
  if (searchTypesObject.value === 'Отправить') {
    cardSend();
    isCardStorage.value = getIsCardStorage();
  } else cardAccept();
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
