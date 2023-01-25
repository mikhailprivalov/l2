<template>
  <div :class="[$style.root, props.withCreating && $style.withCreating]">
    <div :class="$style.filterWrapper">
      <input
        v-model.trim="filter"
        type="text"
        class="form-control nbr"
        :class="$style.filterInput"
        placeholder="Фильтр"
      >
      <span
        v-if="filter"
        :class="$style.clearButton"
        @click="filter = ''"
      ><i class="fa fa-times" /></span>
    </div>

    <div :class="$style.listWrapper">
      <div
        v-if="status !== ApiStatus.SUCCESS"
        :class="$style.loaderWrapper"
      >
        <Spinner />
        <div
          v-if="props.loadingText"
          :class="$style.loaderText"
        >
          {{ props.loadingText }}
        </div>
      </div>
      <template v-else>
        <div
          v-for="e in filteredRows"
          :key="e.id"
          :class="[$style.listItem, e.id === selectedId && $style.listItemSelected, !e.isActive && $style.listItemNotActive]"
          @click="selectedId = e.id"
        >
          {{ e.name }}
        </div>
      </template>
    </div>

    <button
      class="btn btn-blue-nb nbr"
      :class="$style.createButton"
    >
      <i class="glyphicon glyphicon-plus" />
      Добавить
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import Spinner from '@/components/Spinner.vue';
import useApi, { ApiStatus } from '@/api/useApi';

type Id = number | string;
type IdOptional = Id | null;

export interface ListElement {
  id: Id,
  name: string,
  createdAt: string,
  updatedAt: string | null,
  isActive: boolean,
}

const props = defineProps<{
  baseSource: string,
  listRequestParams?: Record<string, any>,
  editUrl?: string,
  value?: Id,
  loadingText?: string,
  withCreating?: boolean,
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', id: IdOptional): void
}>();

const { data, status } = useApi<{rows: ListElement[]}>({
  path: `${props.baseSource}/list`,
  data: props.listRequestParams,
}, { defaultData: { rows: [] } });

const selectedId = ref<IdOptional>(null);

watch(
  selectedId,
  () => {
    emit('input', selectedId.value);
  },
);

const filter = ref('');

const filteredRows = computed<ListElement[]>(() => {
  if (filter.value === '') {
    return data.value.rows;
  }
  return data.value.rows.filter(row => row.name.toLowerCase().includes(filter.value.toLowerCase()));
});
</script>

<style lang="scss" module>
.root {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

.filterWrapper {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 34px;

  .form-control {
    padding-right: 34px;
  }

  .clearButton {
    position: absolute;
    top: 2px;
    right: 2px;
    cursor: pointer;
    bottom: 3px;
    width: 30px;
    opacity: .5;
    line-height: 29px;
    text-align: center;

    &:hover {
      opacity: 1;
      text-shadow: 0 0 2px #049372;
    }
  }
}

.filterInput {
  border-top: 0;
  border-right: 0;
  border-left: 0;
}

.loaderWrapper {
  padding: 10px;
  text-align: center;
}

.loaderText {
  margin-top: 10px;
  color: gray;
}

.listWrapper {
  position: absolute;
  top: 34px;
  right: 0;
  bottom: 0;
  left: 0;
  overflow-x: visible;
  overflow-y: auto;
}

.listItem {
  background-color: #fff;
  padding: 5px;
  margin: 10px;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;

  &:hover {
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 1;
    transform: scale(1.008);
  }
}

.listItemNotActive {
  background-image: linear-gradient(#6c7a89, #56616c);
  color: #fff;
}

.listItemSelected {
  background: linear-gradient(to bottom, #049372bb 0%, #049372ee 100%) !important;
  color: #fff;
}

.withCreating {
  .listWrapper {
    bottom: 34px;
  }
}

.createButton {
  position: absolute;
  bottom: 0;
  right: 0;
  left: 0;
  height: 34px;
}
</style>
