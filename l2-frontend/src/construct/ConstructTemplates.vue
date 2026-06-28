<template>
  <div
    ref="root"
    class="construct-root"
  >
    <div
      v-show="openedId === -2"
      class="construct-sidebar"
    >
      <div class="sidebar-select">
        <SelectPickerM
          v-model="type"
          style="height: 34px;"
          :options="types"
        />
      </div>
      <div
        class="sidebar-content"
        :class="{ fcenter: templatesList.length === 0 }"
      >
        <div v-if="templatesList.length === 0">
          Не найдено
        </div>
        <div
          v-for="row in rows"
          :key="row.pk"
          class="research"
          :class="{ rhide: row.hide }"
          @click="openEditor(row.pk)"
        >
          <div class="t-t">
            {{ row.title }}
          </div>
          <div
            v-for="res in row.researches"
            :key="res.pk"
            class="t-r"
          >
            {{ res.title }}
          </div>
        </div>
      </div>
      <button
        class="btn btn-blue-nb sidebar-footer"
        @click="openEditor(-1)"
      >
        <i class="glyphicon glyphicon-plus" />
        Добавить
      </button>
    </div>
    <div class="construct-content">
      <TemplateEditor
        v-if="openedId > -2"
        style="position: absolute;top: 0;right: 0;bottom: 0;left: 0;"
        :pk="openedId"
        :global_template_p="parseInt(String(type), 10)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, onMounted, onUnmounted, ref, watch,
} from 'vue';

import SelectPickerM from '@/fields/SelectPickerM.vue';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';

import UrlData from '../UrlData';
import TemplateEditor from './TemplateEditor.vue';

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const type = ref(1);
const templatesList = ref<any[]>([]);
const openedId = ref(-2);

const types = computed(() => [
  { value: 1, label: 'Глобальные' },
  { value: 2, label: 'В поиске' },
]);

const rows = computed(() => templatesList.value.map((r) => ({
  ...r,
  researches: r.researches.map((rpk: number) => store.getters.researches_obj[rpk]).filter(Boolean),
})));

let unwatchResearches: (() => void) | null = null;

const loadTemplates = () => {
  templatesList.value = [];
  fetch(`/api/load-templates?type=${type.value}`)
    .then((r) => r.json())
    .then((data) => {
      templatesList.value = data.result;
    });
};

const openEditor = (pk: number) => {
  openedId.value = pk;
};

const cancelEdit = () => {
  openedId.value = -2;
  loadTemplates();
};

watch(type, () => {
  loadTemplates();
});

onMounted(() => {
  const storedData = UrlData.get();
  if (storedData && typeof storedData === 'object' && storedData.pk) {
    openedId.value = storedData.pk;
  }
  root.$on('research-editor:cancel', cancelEdit);

  store.dispatch(actions.INC_LOADING);
  store.dispatch(actions.GET_RESEARCHES).finally(() => {
    store.dispatch(actions.DEC_LOADING);
  });

  unwatchResearches = store.watch(
    (state) => state.researches,
    () => {
      loadTemplates();
    },
  );
});

onUnmounted(() => {
  root.$off('research-editor:cancel', cancelEdit);
  if (unwatchResearches) {
    unwatchResearches();
  }
});
</script>

<style scoped lang="scss">
.construct-root {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;

  display: flex;
  align-items: stretch;
  flex-direction: row;
  flex-wrap: nowrap;
  align-content: stretch;
  & > div {
    align-self: stretch;
  }
}

.construct-sidebar {
  width: 350px;
  border-right: 1px solid #b1b1b1;
  display: flex;
  flex-direction: column;

  .form-control {
    border-radius: 0;
    border-top: none;
    border-left: none;
    border-right: none;
  }
}

.construct-content {
  width: 100%;
  position: relative;
}

.sidebar-select ::v-deep .btn {
  border-radius: 0;
  border-top: none;
  border-left: none;
  border-right: none;
  border-top: 1px solid #fff;
}

.sidebar-select,
.sidebar-filter,
.sidebar-footer {
  flex: 0 0 34px;
}

.sidebar-content {
  height: 100%;
  overflow-y: auto;
  background-color: hsla(30, 3%, 97%, 1);
}

.sidebar-content:not(.fcenter) {
  padding-bottom: 10px;
}

.sidebar-footer {
  border-radius: 0;
  margin: 0;
}

.fcenter {
  display: flex;
  align-items: center;
  justify-content: center;
}

.research {
  background-color: #fff;
  padding: 5px;
  margin: 10px;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;

  &.rhide {
    background-image: linear-gradient(#6c7a89, #56616c);
    color: #fff;
  }

  hr {
  }

  &:hover {
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 1;
    transform: scale(1.008);
  }
}

.research:not(:first-child) {
  margin-top: 0;
}

.research:last-child {
  margin-bottom: 0;
}

.t-t {
  font-weight: bold;
}

.t-r {
  font-size: 80%;
  padding-left: 5px;
}
</style>
