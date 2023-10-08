<script setup lang="ts">
import { ref } from 'vue';

import SearchForm from '@/pages/CaseControl/Sidebar/SearchForm.vue';
import AnamnesisView from '@/pages/CaseControl/Sidebar/AnamnesisView.vue';
import useOn from '@/hooks/useOn';
import useLoader from '@/hooks/useLoader';
import useNotify from '@/hooks/useNotify';
import api from '@/api';
import { Patient } from '@/pages/CaseControl/types';
import directionsPoint from '@/api/directions-point';

import { menuItems } from './menu';

const loader = useLoader();
const notify = useNotify();

const caseTitle = ref<string>('');
const cancel = ref<boolean>(false);
const direction = ref<number | null>(null);
const openedPatient = ref<Patient | null>(null);
const openedTree = ref<any | null>(null);
const childResearch = ref<any | null>(null);
const originalDirection = ref<any | null>(null);
const counts = ref<Record<string, number>>({});

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
    cancel.value = data.cancel;
    childResearch.value = data.childResearch;
    openedPatient.value = patient;
    openedTree.value = tree;
    counts.value = data.counts;
    originalDirection.value = data.originalDirection;
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
useOn('researches-picker:directions_createdcd', loadData);

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
          v-if="!cancel"
          href="#"
          :class="{ cancel_color: !cancel }"
          class="a-under"
          @click.prevent="toggleCancel"
        >
          Отменить
        </a>
        <a
          v-if="cancel"
          href="#"
          :class="{ active_color: cancel }"
          class="a-under"
          @click.prevent="toggleCancel"
        >
          Вернуть
        </a>
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
      </div>
    </div>
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
}

.colorBad {
  background-color: lightblue !important;
  color: #d35400;
}

.counts {
  float: right;
}
</style>
