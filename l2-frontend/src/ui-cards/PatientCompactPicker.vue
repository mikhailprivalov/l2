<template>
  <div class="patient-picker-container">
    <div
      class="top-picker"
      :class="{ internalType: selectedBase.internal_type }"
    >
      <div class="input-group">
        <div class="input-group-btn">
          <button
            class="btn btn btn-blue-nb btn-ell dropdown-toggle no-border-radius dropdown-base-select"
            type="button"
            data-toggle="dropdown"
          >
            {{ props.titleForBase || selectedBase.title }}
          </button>
        </div>
        <div>
          <div class="autocomplete">
            <input
              ref="qRef"
              v-model="query"
              type="text"
              class="form-control input-borderless"
              placeholder="Введите запрос — пример: Иванов Иван 01011970"
              maxlength="255"
              @keyup.enter="search"
              @keypress="keypress"
              @keydown="keypressArrow"
              @click="clickInput"
              @blur="blur"
              @keyup.esc="suggests.open = false"
              @focus="suggestsFocus"
            >
            <div
              class="clear-input"
              :class="{ display: query.length > 0 }"
              @click="clearInput"
            >
              <i class="fa fa-times" />
            </div>
            <div
              v-if="(suggests.open && normalizedQuery.length > 0) || suggests.loading"
              class="suggestions"
            >
              <div
                v-if="suggests.loading && suggests.data.length === 0"
                class="item"
              >
                поиск...
              </div>
              <div
                v-else-if="suggests.data.length === 0"
                class="item"
              >
                не найдено карт в {{ system }}, попробуйте произвести поиск по ТФОМС или РМИС
              </div>
              <template v-else>
                <div
                  v-for="(row, i) in suggests.data"
                  :key="row.pk"
                  class="item item-selectable"
                  :class="{ 'item-selectable-focused': i === suggests.focused }"
                  @mouseover="suggests.focused = i"
                  @click.stop="selectSuggest(i)"
                >
                  {{ row.family }} {{ row.name }} {{ row.twoname }}, {{ row.sex }}, {{ row.birthday }} ({{ row.age }})
                  <div>
                    <span
                      class="font-weight-bold card-number-display"
                    > {{ row.type_title }} {{ row.num }} </span>
                    <span
                      v-for="d in row.docs"
                      :key="d.pk"
                      class="item-doc"
                    >
                      {{ d.type_title }}: {{ d.serial }} {{ d.number }};
                    </span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
        <span
          v-if="tfomsQuery"
          class="rmis-search input-group-btn"
        >
          <label
            class="btn btn-blue-nb no-border-radius height34 checkbox-label"
          >
            <input
              v-model="incTfoms"
              type="checkbox"
            >
            {{ tfomsAsL2 ? 'ЕРЦП' : 'ТФОМС' }}
          </label>
        </span>
        <span
          v-if="selectedBase.internal_type && userData.rmis_enabled"
          class="rmis-search input-group-btn"
        >
          <label
            class="btn btn-blue-nb no-border-radius height34 checkbox-label"
          >
            <input
              v-model="incRmis"
              type="checkbox"
            > Вкл. РМИС
          </label>
        </span>
        <span class="input-group-btn">
          <button
            class="btn action-button btn-blue-nb no-border-radius"
            type="button"
            :disabled="!queryValid || inLoading"
            @click="search({ source: 'button' })"
          >
            Поиск
          </button>
        </span>
      </div>
    </div>
    <div class="content-picker scrolldown">
      <div class="table-container">
        <template v-if="'pk' in selectedCard && selectedCard.pk !== -1">
          <table class="table table-bordered">
            <colgroup>
              <col width="124">
              <col>
              <col width="54">
              <col>
            </colgroup>
            <tbody>
              <tr>
                <td
                  class="table-header-row cell-narrow"
                >
                  ФИО:
                </td>
                <td
                  class="table-content-row cell-wide"
                >
                  {{ selectedCard.family }} {{ selectedCard.name }} {{ selectedCard.twoname }}
                </td>
                <td
                  class="table-header-row cell-medium"
                >
                  {{ selectedCard.is_rmis ? 'ID' : 'Карта' }}:
                </td>
                <td
                  class="table-content-row cell-wide"
                >
                  {{ selectedCard.num }}
                  <span
                    v-if="selectedCard.isArchive"
                    class="is-archive"
                  >в архиве</span>
                </td>
              </tr>
              <tr>
                <td class="table-header-row">
                  Дата рождения:
                </td>
                <td class="table-content-row">
                  {{ selectedCard.birthday }}<span v-if="loaded"> ({{ selectedCard.age }})</span>
                </td>
                <td class="table-header-row">
                  Пол:
                </td>
                <td class="table-content-row">
                  {{ selectedCard.sex }}
                </td>
              </tr>
            </tbody>
          </table>
          <slot
            v-if="loaded"
            name="for_card"
            class="mt-5"
          />
        </template>
        <div
          v-else
          class="empty-state-card-create"
        >
          <div class="empty-state-card-create__content">
            <h3 class="empty-state-card-create__title">
              Карта пациента не выбрана
            </h3>
            <div class="empty-state-card-create__desc">
              Создайте новую карту или воспользуйтесь поиском.
            </div>
          </div>
        </div>
      </div>
    </div>
    <div
      v-if="selectedCard && selectedCard.pk !== -1 && allowL2CardEdit"
      class="bottom-picker"
    >
      <button
        class="btn action-button btn-blue-nb no-border-radius"
        type="button"
        @click="openEditor(true)"
      >
        Новая {{ system }} карта
      </button>
      <button
        class="btn action-button btn-blue-nb no-border-radius ml-negative"
        type="button"
        :disabled="!selectedCard.pk"
        @click="openEditor()"
      >
        Редактировать карту
      </button>
    </div>
    <Modal
      v-if="showModal"
      ref="modal"
      show-footer="true"
      @close="hideModal"
    >
      <span slot="header">Найдено несколько карт</span>
      <div slot="body">
        <div
          v-for="(row, i) in foundedCards"
          :key="row.pk"
          class="founded"
          @click="selectCard(i)"
        >
          <div class="founded-row">
            Карта <span class="font-weight-bold">{{ row.type_title }} {{ row.num }}</span>
          </div>
          <div class="founded-row">
            <span class="font-weight-bold">ФИО, пол:</span> {{ row.family }} {{ row.name }} {{ row.twoname }}, {{ row.sex }}
          </div>
          <div class="founded-row">
            <span class="font-weight-bold">Дата рождения:</span> {{ row.birthday }} ({{ row.age }})
          </div>
          <div
            v-for="d in row.docs"
            :key="d.pk"
            class="founded-row"
          >
            <span class="font-weight-bold">{{ d.type_title }}:</span> {{ d.serial }} {{ d.number }}
          </div>
        </div>
      </div>
      <div
        slot="footer"
        class="text-center"
      >
        <small>Показано не более 10 карт</small>
      </div>
    </Modal>
    <L2CardCreate
      v-if="editorPk !== -2"
      :card_pk="editorPk"
      :base_pk="base"
    />
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  onMounted,
  onUnmounted,
  reactive,
  ref,
  watch,
} from 'vue';
import { debounce } from 'lodash';

import { useStore } from '@/store';
import Modal from '@/ui-cards/Modal.vue';
import L2CardCreate from '@/modals/L2CardCreate.vue';
import * as actions from '@/store/action-types';
import patientsPoint from '@/api/patients-point';
import { SimplePatient } from '@/types/patient';
import { Base } from '@/types/cards';

const tfomsRe = /^([А-яЁё-]+) ([А-яЁё-]+)( ([А-яЁё-]+))? (([0-9]{2})\.?([0-9]{2})\.?([0-9]{4}))$/;

interface SuggestsState {
  focused: number;
  open: boolean;
  loading: boolean;
  data: SimplePatient[];
}

const props = defineProps({
  search_results: {
    default: 'false',
    type: String,
  },
  value: {},
  titleForBase: {
    type: String,
    required: false,
  },
});

const emit = defineEmits(['input']);

const store = useStore();
const instance = getCurrentInstance();
// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
const root = instance!.proxy.$root;

const base = ref<number>(-1);
const query = ref('');
const showModal = ref(false);
const foundedCards = ref<SimplePatient[]>([]);
const selectedCard = reactive<Partial<SimplePatient>>({});
const loaded = ref(false);
const searchAfterLoading = ref(false);
const openEditAfterLoading = ref(false);
const editorPk = ref(-2);
const incRmis = ref(false);
const incTfoms = ref(false);
const suggests = reactive<SuggestsState>({
  focused: -1,
  open: false,
  loading: false,
  data: [],
});

const qRef = ref<HTMLInputElement | null>(null);

// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
const system = computed(() => instance!.proxy.$systemTitle());

const bases = computed<Base[]>(() => store.getters.bases.filter((b: Base) => b.internal_type && !b.hide));

const selectedBase = computed<Base>(() => {
  const found = bases.value.find((b) => b.pk === base.value);
  return (
    found || {
      title: 'Не выбрана база',
      pk: -1,
      code: '',
      hide: false,
      history_number: false,
      fin_sources: [],
      internal_type: true,
    }
  );
});

const fixedQuery = computed(() => query.value
  .split(' ')
  .map((s) => s
    .split('-')
    .map((x) => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase())
    .join('-'))
  .join(' '));

const l2Tfoms = computed(() => store.getters.modules.l2_tfoms);

const normalizedQuery = computed(() => fixedQuery.value.trim());
const tfomsQuery = computed(() => selectedBase.value.internal_type && l2Tfoms.value && !!normalizedQuery.value.match(tfomsRe));
const queryValid = computed(() => normalizedQuery.value.length > 0);

const forceRmisSearch = computed(() => Boolean(store.getters.modules.l2_force_rmis_search));
const tfomsAsL2 = computed(() => Boolean(store.getters.modules.l2_tfoms_as_l2));
const autoClinicalExaminationDirect = computed(() => Boolean(store.getters.modules.auto_clinical_examination_direct));

const userData = computed(() => store.getters.user_data);

const isOperator = computed(() => Array.isArray(userData.value.groups)
  && userData.value.groups.includes('Оператор лечащего врача'));
const isDoc = computed(() => Array.isArray(userData.value.groups)
  && userData.value.groups.includes('Лечащий врач'));

const inLoading = computed(() => store.getters.inLoading);

const allowL2CardEdit = computed(
  () => userData.value.su
    || userData.value.groups?.includes('Картотека')
    || userData.value.groups?.includes('Картотека L2'),
);

function emitInput(fromHn = false) {
  const pk = 'pk' in selectedCard ? (selectedCard as any).pk : -1;
  emit('input', pk);
  if (pk !== -1 && !fromHn) {
    window.$('#fndsrc').focus();
  }
}

const focusInput = () => {
  // eslint-disable-next-line no-unused-expressions
  qRef.value && window.$(qRef.value).focus();
};

function checkBase() {
  if (base.value === -1 && bases.value.length > 0) {
    base.value = bases.value[0].pk;
    emitInput();
    setTimeout(focusInput, 200);
  }
}

function hideModal() {
  showModal.value = false;
  const modalComp: any = (instance as any).refs?.modal;
  if (modalComp?.$el) {
    modalComp.$el.style.display = 'none';
  }
}

function selectCard(index: number) {
  hideModal();
  suggests.open = false;
  suggests.loading = false;
  suggests.data = [];
  Object.assign(selectedCard, foundedCards.value[index]);

  if ((selectedCard as any).base_pk) {
    if (base.value && base.value !== (selectedCard as any).base_pk) {
      query.value = '';
    }
    base.value = (selectedCard as any).base_pk;
  }
  emitInput();
  loaded.value = true;
  root.$emit('patient-picker:select_card');

  setTimeout(() => {
    if (
      !autoClinicalExaminationDirect.value
      || !isOperator.value
      || !isDoc.value
    ) {
      return;
    }

    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    const pks = selectedCard.disp_data?.filter((d: any) => !d[2]).map((d: any) => d[0]) || [];
    if (pks.length === 0) return;
    root.$emit('msg', 'ok', 'Добавлены назначения по диспансеризации');
  }, 100);
}

function moveFocus(d: number) {
  suggests.focused += d;
  if (suggests.focused < -1) {
    suggests.focused = suggests.data.length - 1;
  } else if (suggests.focused > suggests.data.length - 1) {
    suggests.focused = -1;
  }
}

async function loadSuggests() {
  if (normalizedQuery.value.length === 0) {
    suggests.open = false;
    suggests.loading = false;
    suggests.data = [];
    return;
  }
  suggests.loading = true;
  suggests.open = true;

  suggests.data = (
    await patientsPoint.searchCard({
      type: base.value,
      query: normalizedQuery.value,
      list_all_cards: false,
      inc_rmis: false,
      inc_tfoms: false,
      suggests: true,
    })
  ).results;

  if (suggests.data.length === 0) {
    suggests.focused = -1;
  }

  moveFocus(0);
  suggests.loading = false;
}

const keypressOther = debounce((e: KeyboardEvent) => {
  if (e.keyCode !== 27 && e.keyCode !== 13) {
    loadSuggests();
  }
}, 200);

function keypressArrow(e: KeyboardEvent) {
  if (e.keyCode === 38) {
    moveFocus(-1);
    e.preventDefault();
    e.stopPropagation();
    (e as any).cancelBubble = true;
    return true;
  }
  if (e.keyCode === 40) {
    moveFocus(1);
    e.preventDefault();
    e.stopPropagation();
    (e as any).cancelBubble = true;
    return true;
  }
  return false;
}

function keypress(e: KeyboardEvent) {
  if (!keypressArrow(e)) {
    keypressOther(e);
  }
}

function blur() {
  query.value = fixedQuery.value;
  setTimeout(() => {
    suggests.open = false;
  }, 200);
}

function suggestsFocus() {
  if (normalizedQuery.value.length === 0) return;
  suggests.focused = -1;
  suggests.open = true;
  if ((selectedCard as any).pk && qRef.value) {
    qRef.value.setSelectionRange(0, query.value.length);
  }
}

function selectSuggest(i: number) {
  foundedCards.value = suggests.data;
  window.$('input').each(function () {
    window.$(this).trigger('blur');
  });
  selectCard(i);
}

function clearInput() {
  query.value = '';
  if (qRef.value) window.$(qRef.value).focus();
}

function clickInput() {
  loadSuggests();
}

function openEditor(isnew?: boolean) {
  if (isnew) {
    editorPk.value = -1;
  } else {
    editorPk.value = (selectedCard as any).pk;
  }
}

function clear() {
  loaded.value = false;
  Object.keys(selectedCard).forEach((k) => delete (selectedCard as any)[k]);
  foundedCards.value = [];
  if (query.value.toLowerCase().includes('card_pk:') || query.value.toLowerCase().includes('phone:')) {
    query.value = '';
  }
  emitInput();
}

function search(args?: { source: string }) {
  const source = args?.source || 'js';
  if (!queryValid.value || inLoading.value) return;
  suggests.open = false;
  suggests.loading = false;
  if (suggests.focused > -1 && suggests.data.length > 0 && source !== 'button') {
    selectSuggest(suggests.focused);
    return;
  }
  suggests.data = [];
  const q = query.value;
  checkBase();
  window.$('input').each(function () {
    window.$(this).trigger('blur');
  });
  store.dispatch(actions.ENABLE_LOADING, { loadingLabel: 'Поиск карты' });
  patientsPoint
    .searchCard({
      type: base.value,
      query: q,
      list_all_cards: false,
      inc_rmis: incRmis.value || searchAfterLoading.value,
      inc_tfoms: incTfoms.value && tfomsQuery.value,
    })
    .then((result: any) => {
      clear();
      if (result.results) {
        foundedCards.value = result.results;
        if (foundedCards.value.length > 1) {
          showModal.value = true;
        } else if (foundedCards.value.length === 1) {
          selectCard(0);
          if (openEditAfterLoading.value) openEditor();
        } else {
          root.$emit('msg', 'error', 'Карт по такому запросу не найдено');
        }
      } else {
        root.$emit('msg', 'error', 'Ошибка на сервере');
      }
      if (searchAfterLoading.value) {
        searchAfterLoading.value = false;
        query.value = '';
      }
    })
    .catch((error: any) => {
      root.$emit('msg', 'error', `Ошибка на сервере\n${error.message}`);
    })
    .finally(() => {
      openEditAfterLoading.value = false;
      store.dispatch(actions.DISABLE_LOADING);
    });
}

async function inited() {
  await store.dispatch(actions.INC_LOADING);
  // eslint-disable-next-line no-constant-condition
  while (true) {
    if (!store.getters.user_data.loading) break;
    await new Promise((r) => {
      setTimeout(r, 10);
    });
  }
  await store.dispatch(actions.DEC_LOADING);
  checkBase();
}

watch(forceRmisSearch, () => {
  incRmis.value = forceRmisSearch.value;
}, { immediate: true });

watch(normalizedQuery, () => {
  keypressOther({ keyCode: -1 } as any);
});

watch(bases, checkBase);
watch(isOperator, emitInput);

watch(inLoading, (val) => {
  if (!val && searchAfterLoading.value) {
    search();
  }
});

watch(tfomsQuery, (nv) => {
  if (nv) incTfoms.value = true;
});

watch(base, (nv) => {
  root.$emit('global:select-base', nv);
  window.localStorage.setItem('selected-base', String(nv));
}, { immediate: true });

onMounted(() => {
  inited();
  store.watch(
    (state: any) => state.bases,
    () => {
      checkBase();
    },
    { immediate: true },
  );

  const searchHandler = () => search();
  const searchValueHandler = (value: string) => {
    query.value = value;
    search();
  };
  const selectCardHandler = (data: any) => {
    base.value = data.base_pk;
    query.value = `card_pk:${data.card_pk}:${data.inc_archive || false}`;
    searchAfterLoading.value = true;
    if (qRef.value) window.$(qRef.value).focus();
    emitInput();
    if (!data.hide) {
      editorPk.value = data.card_pk;
    } else {
      editorPk.value = -2;
    }
    setTimeout(() => {
      search();
      if (!data.hide) {
        setTimeout(() => {
          root.$emit('reload_editor');
        }, 5);
      }
    }, 5);
  };
  const hideEditorHandler = () => {
    editorPk.value = -2;
  };

  root.$on('search', searchHandler);
  root.$on('search-value', searchValueHandler);
  root.$on('select_card', selectCardHandler);
  root.$on('hide_l2_card_create', hideEditorHandler);

  onUnmounted(() => {
    root.$off('search', searchHandler);
    root.$off('search-value', searchValueHandler);
    root.$off('select_card', selectCardHandler);
    root.$off('hide_l2_card_create', hideEditorHandler);
  });
});
</script>

<style scoped lang="scss">
table {
  table-layout: fixed;
  padding: 0;
  margin: 5px 0 0;
}

td:not(.select-td):not(.cl-td) {
  padding: 2px !important;
}

.table-header-row {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
}

.table-content-row:not(.cl-td) {
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
}

.content-picker {
  position: absolute;
  top: 34px;
  left: 0;
  right: 0;
  bottom: 34px;
  overflow-y: auto;
  overflow-x: hidden;
}

.top-picker {
  height: 34px;
  background-color: #aab2bd;
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  white-space: nowrap;
}

.bottom-picker {
  height: 34px;
  background-color: #aab2bd;
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  white-space: nowrap;
  display: flex;
  flex-direction: row;
  justify-content: flex-end;
}

.bottom-picker {
  bottom: 0;
}

.dropdown-menu {
  max-width: 350px;
  min-width: 1%;
}

.patient-picker-container {
  height: 100%;
  width: 100%;
  position: relative;
}

.dropdown-base-select {
  max-width: 200px;
  text-align: left !important;
}

.checkbox-label {
  padding: 5px 12px;
}

.table-container {
  padding-left: 5px;
  padding-right: 5px;
}

.cell-narrow {
  max-width: 124px;
}

.cell-wide {
  max-width: 99%;
}

.cell-medium {
  max-width: 54px;
}

.ml-negative {
  margin-left: -1px;
}

.mt-5 {
  margin-top: 5px;
}

.font-weight-bold {
  font-weight: bold;
}

.card-number-display {
  display: inline-block;
  margin-right: 4px;
}

.empty-state-card-create {
  height: 190px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  margin: 10px 10px 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.07);
  position: relative;
  &__content {
    text-align: center;
    width: 100%;
  }
  &__title {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 10px;
  }
  &__desc {
    font-size: 14px;
    color: #5a5a5a;
    margin-bottom: 22px;
    line-height: 1.5;
  }
  &__button {
    font-weight: 600;
    i {
      margin-right: 8px;
    }
  }
}
</style>

<style lang="scss">
.call-padding-right {
  padding-right: 15px;
}

.call-padding-top {
  padding-top: 20px;
}

.select-td {
  padding: 0 !important;

  .bootstrap-select {
    height: 38px;
    display: flex !important;

    button {
      border: none !important;
      border-radius: 0 !important;

      .filter-option {
        text-overflow: ellipsis;
      }
    }
  }
}

.input-borderless {
  border-left: none !important;
  border-top: none !important;
  border-right: none !important;
}

.hospital input {
  border-radius: 0;
}

.dropdown-toggle-button {
  max-width: 200px;
  min-width: 60px;
  text-align: left !important;
}

.autocomplete {
  position: relative;
  overflow: visible;
  height: 34px;

  input {
    border-radius: 0;
  }

  .suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #fff;
    border-radius: 0 0 5px 5px;
    border: 1px solid #3bafda;
    border-top: none;
    box-shadow: 0 10px 20px rgba(#3bafda, 0.19), 0 6px 6px rgba(#3bafda, 0.23);
    overflow: hidden;
    z-index: 1000;

    .item {
      padding: 3px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      word-break: keep-all;

      &-doc {
        color: #888;
        font-size: 85%;
      }

      &-selectable {
        cursor: pointer;
        &-focused {
          background: rgba(#3bafda, 0.1);
        }
      }
    }
  }

  .clear-input {
    display: none;
    position: absolute;
    cursor: pointer;
    top: 0;
    right: 0;
    width: 34px;
    height: 34px;
    opacity: 0.6;

    &:hover {
      background: rgba(0, 0, 0, 0.15);
      opacity: 1;
    }

    &.display {
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 10;
    }
  }
}

.error-row {
  color: #f00;
}

.no-border-radius {
  border-radius: 0;
}

.action-button {
  min-width: 40px;
}
</style>
