<template>
  <div class="request-history-root">
    <div class="request-history-sidebar">
      <div class="sidebar-top">
        <div class="input-group">
          <span class="input-group-btn relative">
            <button
              class="btn btn-blue-nb btn-ell dropdown-toggle bt1"
              type="button"
              @click="showModes = !showModes"
            >
              <span class="caret" />
              {{ SEARCH_MODES_MAP.get(searchMode) }}
              <i
                v-if="isLoading"
                class="fa fa-spinner"
              />
            </button>
            <ul
              v-show="showModes"
              class="dropdown-menu min-width-160 margin-top-1"
            >
              <li
                v-for="row in SEARCH_MODES"
                v-if="row.id !== searchMode"
                :key="row.id"
              >
                <a
                  href="#"
                  :class="{ 'mode-active': searchMode === row.id }"
                  @click.prevent="selectMode(row.id)"
                >{{ row.title }}</a>
              </li>
            </ul>
          </span>
          <DateFieldNav
            :def="selectedDate"
            :val.sync="selectedDate"
            w="100px"
            light
          />
        </div>
      </div>
      <div class="directions">
        <div class="inner">
          <div
            v-for="item in requests"
            :key="item.id"
            class="direction"
          >
            <div>{{ item.patient }}</div>
            <div class="research-row">
              <div class="row">
                <div class="col-xs-7">
                  {{ item.datetime }}
                </div>
                <div class="col-xs-5 text-right">
                  <span
                    class="image-status"
                    :class="item.hasImage ? 'image-status--yes' : 'image-status--no'"
                  >
                    {{ item.hasImage ? 'Снимок есть' : 'Без снимка' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="requests.length === 0 && !isLoading"
            class="text-center margin-5"
          >
            Нет данных
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, ref, watch,
} from 'vue';
import moment from 'moment';

import api from '@/api';
import DateFieldNav from '@/fields/DateFieldNav.vue';
import useNotify from '@/hooks/useNotify';

const props = defineProps<{ cardId?: number | null }>();
const notify = useNotify();

const SEARCH_MODES = [
  { id: 'all', title: 'Все заявки' },
  { id: 'card', title: 'Пациент' },
];

const SEARCH_MODES_MAP = new Map(SEARCH_MODES.map((m) => [m.id, m.title]));

const searchMode = ref(SEARCH_MODES[0].id);
const selectedDate = ref(moment().format('DD.MM.YYYY'));
const showModes = ref(false);
const isLoading = ref(false);

const selectMode = (id: string) => {
  searchMode.value = id;
  showModes.value = false;
};

type Request = {
  id: number;
  patient: string;
  datetime: string;
  hasImage: boolean;
  cardId: number;
};

const requests = ref<Request[]>([]);

const actualCardId = computed(() => {
  if (searchMode.value === 'card' && props.cardId && props.cardId > 0) {
    return props.cardId;
  }
  return null;
});

const getRequests = async () => {
  isLoading.value = true;
  try {
    const { rows } = await api('requests/list', {
      date: selectedDate.value,
      searchType: searchMode.value,
      cardId: actualCardId.value,
    });
    requests.value = rows;
  } catch (error) {
    notify.error('Ошибка при получении заявок');
  } finally {
    isLoading.value = false;
  }
};

watch([selectedDate, searchMode, actualCardId], async () => {
  await getRequests();
}, { immediate: true });
</script>

<style scoped lang="scss">
.request-history-root {
  display: flex;
  flex-direction: row;
  height: 100%;
}
.request-history-sidebar {
  width: 100%;
  display: flex;
  flex-direction: column;
}
.sidebar-top {
  background: #eaeaea;

  ::v-deep input {
    border-bottom: 1px solid #b1b1b1;
  }
}
.input-group {
  display: flex;
  align-items: center;
}
.input-group-btn {
  position: relative;
  display: flex;
  align-items: center;
  width: 119px;

  button {
    width: 100%;
    text-align: left;
  }
}
.relative {
  position: relative;
}
.btn {
  border-radius: 0;
  padding: 6px;
  font-size: 12px;
  height: 34px;
  background: #049372;
  color: #fff;
  border: none;
}
.dropdown-toggle {
  cursor: pointer;
}
.dropdown-menu {
  position: absolute;
  left: 0;
  top: 100%;
  z-index: 1000;
  display: block;
  float: left;
  min-width: 160px;
  padding: 5px 0;
  margin: 2px 0 0;
  font-size: 14px;
  text-align: left;
  list-style: none;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 6px 12px rgba(0,0,0,.175);
}
.min-width-160 {
  min-width: 160px;
}
.margin-top-1 {
  margin-top: 1px;
}
.dropdown-menu li a {
  display: block;
  padding: 3px 20px;
  clear: both;
  font-weight: 400;
  white-space: nowrap;
  text-decoration: none;
}
.mode-active {
  font-weight: bold !important;
}
.sidebar-bottom-top {
  background-color: #eaeaea;
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 0 8px;
  height: 34px;
}
.directions {
  position: relative;
  height: calc(100% - 68px);
  padding-bottom: 34px;
  display: flex;
  flex-direction: column;
}
.directions .inner {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}
.direction {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
}
.research-row {
  margin-top: 3px;
  margin-bottom: 3px;
  padding: 3px;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
}
.image-status {
  font-size: 14px;
  font-weight: 500;
}
.image-status--yes {
  color: #2ecc40;
}
.image-status--no {
  color: #888;
}
.text-center {
  color: #aaa;
  font-style: italic;
  padding: 10px 0;
}
.margin-5 {
  margin: 5px;
}
</style>
