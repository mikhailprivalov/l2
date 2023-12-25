<script setup lang="ts">
import { computed, ref } from 'vue';

import SearchForm from '@/pages/CaseControl/Sidebar/SearchForm.vue';
import AnamnesisView from '@/pages/CaseControl/Sidebar/AnamnesisView.vue';
import useOn from '@/hooks/useOn';
import useLoader from '@/hooks/useLoader';
import useNotify from '@/hooks/useNotify';
import api from '@/api';
import { Patient } from '@/pages/CaseControl/types';
import directionsPoint from '@/api/directions-point';
import Modal from '@/ui-cards/Modal.vue';
import ResearchesPicker from '@/ui-cards/ResearchesPicker.vue';
import SelectedResearches from '@/ui-cards/SelectedResearches.vue';
import LastResult from '@/ui-cards/LastResult.vue';
import { useStore } from '@/store';

import { menuItems, showPlus } from './menu';

const loader = useLoader();
const notify = useNotify();
const store = useStore();

const caseTitle = ref<string>('');
const cancel = ref<boolean>(false);
const direction = ref<number | null>(null);
const iss = ref<number | null>(null);
const finId = ref<number | null>(null);
const openedPatient = ref<Patient | null>(null);
const openedTree = ref<any | null>(null);
const childResearch = ref<any | null>(null);
const originalDirection = ref<any | null>(null);
const counts = ref<Record<string, number>>({});
const isClosed = ref(false);
const plusView = ref<string | null>(null);
const plusOpened = ref(false);
const createResearches = ref<number[]>([]);

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'open-case', id: number): void
  (e: 'open-direction', data: {case: number, view: string, id: number}): void
  (e: 'open-view', view: string): void
}>();

const loadData = async (q?: string) => {
  loader.inc();
  const { ok, message, data } = await api('cases/search', { q: q || direction.value });
  if (ok) {
    const { patient, tree } = data;
    if (message) {
      notify.info(message);
    }
    caseTitle.value = data.caseTitle;
    direction.value = data.direction;
    iss.value = data.iss;
    finId.value = data.fin_pk;
    cancel.value = data.cancel;
    childResearch.value = data.childResearch;
    openedPatient.value = patient;
    openedTree.value = tree;
    counts.value = data.counts;
    originalDirection.value = data.originalDirection;
    isClosed.value = data.closed;
  }
  loader.dec();

  return { ok, message, data };
};

const onSearch = async (q: string, onResult: (ok, message) => void) => {
  const { ok, message, data } = await loadData(q);
  if (!ok) {
    onResult(false, message || `${q}: не найдено`);
  } else {
    onResult(true, `Загружен случай ${direction.value}${Number(q) === direction.value ? '' : ` (поиск по направлению ${q})`}`);
    if (message) {
      notify.info(message);
    }

    if (data.originalDirection?.id && data.originalDirection?.open) {
      setTimeout(() => {
        emit('open-direction', {
          case: data.direction,
          view: data.originalDirection.view,
          id: data.originalDirection.id,
        });
      }, 0);
    } else {
      emit('open-case', direction.value);
    }
  }
};

useOn('result-saved', loadData);
useOn('change-document-state', loadData);
useOn('researches-picker:directions_createdcase', loadData);

const toggleCancel = async () => {
  loader.inc();
  const { cancel: result } = await directionsPoint.cancelDirection({ pk: direction.value });
  cancel.value = result;
  loader.dec();
};

const openView = (view: string) => {
  emit('open-view', view);
};
const openDirection = (view: string, id: number) => {
  emit('open-direction', {
    case: direction.value,
    view,
    id,
  });
};

const openClosing = () => {
  openDirection('closing', direction.value);
};

const plus = (view: string) => {
  plusView.value = view;
  plusOpened.value = true;
};

const plusClose = (view: string) => {
  plusOpened.value = false;
};

const pickerTypesOnly = computed(() => {
  if (plusView.value === 'laboratory') {
    return [2];
  }
  if (plusView.value === 'paraclinical') {
    return [3];
  }
  if (plusView.value === 'morfology') {
    return [10000];
  }
  if (plusView.value === 'consultation') {
    return [4];
  }
  if (plusView.value === 'forms') {
    return [11];
  }
  return [];
});

const basesObj = computed(() => store.getters.bases.reduce(
  (a, b) => ({
    ...a,
    [b.pk]: b,
  }),
  {},
));
</script>

<template>
  <div :class="$style.root">
    <SearchForm @search="onSearch" />
    <div
      v-if="openedPatient"
      :class="$style.sidebarContent"
    >
      <div :class="$style.innerCard">
        {{ caseTitle }}
        <del v-if="cancel"> {{ direction }}</del>
        <span v-else> <code>{{ direction }}</code></span>
        &nbsp;
        <a
          v-if="!cancel && !isClosed"
          href="#"
          :class="{ cancel_color: !cancel }"
          class="a-under"
          @click.prevent="toggleCancel"
        >
          Отменить
        </a>
        <a
          v-if="cancel && !isClosed"
          href="#"
          :class="{ active_color: cancel }"
          class="a-under"
          @click.prevent="toggleCancel"
        >
          Вернуть
        </a>
        <span v-if="isClosed">
          закрыт <i class="fa fa-check-circle-o" />
        </span>
      </div>
      <div
        v-if="childResearch"
        :class="$style.innerCard"
      >
        Первичный приём случая:<br>
        <a
          href="#"
          class="a-under"
          @click.prevent="openDirection(originalDirection?.view || 'consultation', childResearch.direction)"
        >
          {{ childResearch.title }} ({{ childResearch.direction }})
        </a>
      </div>
      <div
        v-if="cancel"
        :class="$style.innerCard"
      >
        <strong>Случай отменён</strong>
      </div>
      <div
        :class="$style.innerCard"
      >
        <a
          :href="`/ui/directions?card_pk=${openedPatient.cardPk}&base_pk=${openedPatient.base}`"
          target="_blank"
          class="a-under"
        >
          {{ openedPatient.fioWithAge }}
        </a>
      </div>
      <div
        :class="$style.innerCard"
      >
        <AnamnesisView :card-pk="openedPatient.cardPk" />
      </div>
      <div
        v-for="(title, key) in menuItems"
        :key="key"
        :class="$style.sidebarBtnWrapper"
      >
        <button
          class="btn btn-blue-nb"
          :class="$style.sidebarBtn"
          @click="openView(key)"
        >
          <span
            v-if="Boolean(counts[key])"
            :class="$style.counts"
          >{{ counts[key] }} шт.</span> {{ title }}
        </button>
        <button
          v-if="showPlus[key] && !isClosed"
          class="btn btn-blue-nb"
          :class="$style.sidebarBtn"
          @click="plus(key)"
        >
          <i class="fa fa-plus" />
        </button>
      </div>
      <div
        key="closing"
        :class="$style.sidebarBtnWrapper"
      >
        <button
          class="btn btn-blue-nb"
          :class="$style.sidebarBtn"
          @click="openClosing"
        >
          {{ isClosed ? 'Протокол закрытия' : 'Закрыть случай' }}
        </button>
      </div>
    </div>

    <MountingPortal
      mount-to="#portal-place-modal"
      name="DirectoryRowEditor"
      append
    >
      <transition name="fade">
        <Modal
          v-if="plusOpened"
          margin-left-right="auto"
          margin-top="60px"
          max-width="1400px"
          show-footer="true"
          white-bg="true"
          width="100%"
          @close="plusClose"
        >
          <span slot="header">Создание направлений – случай {{ direction }}, {{ openedPatient.fioWithAge }}</span>
          <div
            slot="body"
            class="registry-body"
            style="min-height: 140px"
          >
            <div class="row">
              <div
                class="col-xs-6"
                style="height: 450px; border-right: 1px solid #eaeaea; padding-right: 0"
              >
                <ResearchesPicker
                  v-model="createResearches"
                  :types-only="pickerTypesOnly"
                  kk="case"
                  style="border-top: 1px solid #eaeaea; border-bottom: 1px solid #eaeaea"
                />
              </div>
              <div
                class="col-xs-6"
                style="height: 450px; padding-left: 0"
              >
                <SelectedResearches
                  kk="case"
                  :base="basesObj[openedPatient.base]"
                  :researches="createResearches"
                  :valid="true"
                  :card_pk="openedPatient.cardPk"
                  :initial_fin="finId"
                  :parent_iss="iss"
                  :parent-case="direction"
                  :clear_after_gen="true"
                  case-by-direction
                  style="border-top: 1px solid #eaeaea; border-bottom: 1px solid #eaeaea"
                />
              </div>
            </div>
            <div
              v-if="createResearches.length > 0"
              style="margin-top: 5px; text-align: left"
            >
              <table class="table table-bordered lastresults">
                <colgroup>
                  <col width="180">
                  <col>
                  <col width="110">
                  <col width="110">
                </colgroup>
                <tbody>
                  <LastResult
                    v-for="p in createResearches"
                    :key="p"
                    :individual="openedPatient.individualPk"
                    :parent-iss="iss"
                    :no-scroll="true"
                    :research="p"
                  />
                </tbody>
              </table>
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-4">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  @click="plusClose"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
  </div>
</template>

<script lang="ts">
export default {
  name: 'CaseSidebar',
};
</script>

<style module lang="scss">
.root {
  display: flex;
  flex-direction: column;
}

.sidebarContent {
  position: relative;
  height: calc(100% - 34px);
}

.inner {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;

  &Card {
    width: 100%;
    background: #fff;
    border-bottom: 1px solid #b1b1b1 !important;
    padding: 4px 12px;

    &Select {
      font-size: 12px;
      padding: 0;
    }
  }
}

.sidebarBtnWrapper {
  display: flex;
  flex-direction: row;

  .sidebarBtn:first-child {
    flex: 1 1 auto;
  }
}

.sidebarBtn {
  border-radius: 0;
  text-align: left;

  border-top: none !important;
  border-right: none !important;
  border-left: none !important;
  padding: 0 12px;
  height: 24px;

  &:not(:hover):not(.colorBad) {
    cursor: default;
    background-color: rgba(#000, 0.02) !important;
    color: #000;
    border-bottom: 1px solid #b1b1b1 !important;
  }

  &:hover {
    border: none !important;
  }

  &.btn {
    &:active, &:focus {
      border: none !important;
    }
  }
}

.colorBad {
  background-color: lightblue !important;
  color: #d35400;
}

.counts {
  float: right;
}
</style>
