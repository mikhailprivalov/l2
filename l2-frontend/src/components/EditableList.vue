<template>
  <div
    :class="[
      $style.root,
      props.withCreating && $style.withCreating,
      props.withNameFilter && $style.withNameFilter,
      props.selectable && $style.selectable
    ]"
  >
    <div
      v-if="props.withNameFilter"
      :class="$style.filterWrapper"
    >
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
        v-if="isLoading"
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
          @click="select(e.id)"
        >
          <span
            v-if="props.withCreating"
            :class="$style.editButton"
            @click.stop="openEdit(e.id)"
          ><i class="fa fa-pencil" /></span>
          {{ getName(e) }}
        </div>
      </template>
    </div>

    <button
      v-if="props.withCreating"
      class="btn btn-blue-nb nbr"
      :class="$style.createButton"
      @click="openEdit(null)"
    >
      <i class="glyphicon glyphicon-plus" />
      {{ props.addText || 'Добавить' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import Spinner from '@/components/Spinner.vue';

export type Id = number | string;
export type IdOptional = Id | null;

export interface ListElement {
  id: Id,
  name: string,
  createdAt: string,
  updatedAt: string | null,
  isActive: boolean,
  [key: string]: any,
}

export interface ViewParams {
  listName: string,
}

const props = defineProps<{
  rows: ListElement[],
  value?: Id,
  loadingText?: string,
  addText?: string,
  withCreating?: boolean,
  withNameFilter?: boolean,
  selectable?: boolean,
  isLoading?: boolean,
  viewParams?: ViewParams,
}>();

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', id: IdOptional): void
  (e: 'edit', id: IdOptional): void
}>();

const selectedId = ref<IdOptional>(null);

watch(
  selectedId,
  () => {
    emit('input', selectedId.value);
  },
);

const inputValue = computed(() => props.value);
watch(
  inputValue,
  () => {
    if (selectedId.value !== inputValue.value) {
      selectedId.value = inputValue.value;
    }
  },
  {
    immediate: true,
  },
);

const select = (id: Id) => {
  if (props.selectable) {
    selectedId.value = id;
  }
};

const openEdit = (id: IdOptional) => {
  emit('edit', id);
};

const filter = ref('');

const rows = computed<ListElement[]>(() => {
  if (Array.isArray(props.rows)) {
    return props.rows;
  }

  return [];
});

const filteredRows = computed<ListElement[]>(() => {
  if (filter.value === '') {
    return rows.value;
  }
  return rows.value.filter(row => row.name.toLowerCase().includes(filter.value.toLowerCase()));
});

const nameProp = computed(() => props.viewParams?.listName || 'name');

const getName = (e: ListElement) => e[nameProp.value];
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
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  overflow-x: visible;
  overflow-y: auto;
}

.withNameFilter {
  .listWrapper {
    top: 34px;
  }
}

.listItem {
  background-color: #fff;
  padding: 5px;
  margin: 10px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
}

.selectable .listItem {
  cursor: pointer;

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

.editButton {
  cursor: pointer;
  color: #56616c;
  float: right;
  display: inline-block;
  padding: 3px;
  margin-top: -3px;

  &:hover {
    color: #049372;
  }
}

.listItemSelected, .listItemNotActive {
  .editButton {
    opacity: .6;
    color: #ffffff;

    &:hover {
      color: #ffffff;
      opacity: 1;
    }
  }
}
</style>
