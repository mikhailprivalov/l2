<template>
  <div
    :class="[`formulate-input-element formulate-input-element--${context.class}`, $style.container]"
    :data-type="context.type"
  >
    <Treeselect
      :key="key"
      v-model="model"
      :multiple="false"
      :disable-branch-nodes="true"
      class="treeselect-wide treeselect-34px"
      :async="true"
      :append-to-body="true"
      :clearable="true"
      :z-index="5001"
      placeholder="Значение"
      :load-options="loadOptions"
      loading-text="Загрузка"
      no-results-text="Не найдено"
      search-prompt-text="Начните писать для поиска"
      :cache-options="false"
      :open-on-focus="true"
      :default-options="defaultOptions"
      v-bind="context.attributes"
    />
    <button
      v-if="model"
      v-tippy
      type="button"
      class="btn btn-primary-nb btn-blue-nb"
      title="Редактировать"
      @click="edit"
    >
      <i class="fa fa-pencil" />
    </button>
    <button
      v-tippy
      type="button"
      class="btn btn-primary-nb btn-blue-nb"
      title="Добавить"
      @click="add"
    >
      <i class="fa fa-plus" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import Treeselect, { ASYNC_SEARCH } from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import api from '@/api';
import { EDIT_OPEN } from '@/store/action-types';
import { useStore } from '@/store';

const store = useStore();

const props = defineProps<{
  context: Record<any, any>,
  formType: string,
}>();

const hasInit = ref(false);
const defaultOptions = ref<any>([{ id: props.context.model, label: 'загрузка...' }]);
const model = ref<any>(props.context.model);
const key = ref(0);
const initiatorHasRead = ref(false);
const initiator = computed(() => store.getters.editInitiator);
const editPrevEditId = computed(() => store.getters.editPrevEditId);

watch([model, initiatorHasRead], async () => {
  if (hasInit.value || !initiatorHasRead.value) {
    return;
  }

  hasInit.value = true;

  if (model.value) {
    const { result: { rows } } = await api('/edit-forms/objects/search', {
      asTreeselect: true,
      formType: props.formType,
      filters: {
        id: model.value,
      },
    });

    defaultOptions.value = rows;
  } else {
    model.value = undefined;
    defaultOptions.value = undefined;
  }

  key.value += 1;
}, {
  immediate: true,
});

watch(model, async () => {
  if (!hasInit.value) {
    return;
  }

  // eslint-disable-next-line vue/no-mutating-props
  props.context.model = model.value;
});

const loadOptions = async ({ action, searchQuery, callback }) => {
  if (action === ASYNC_SEARCH) {
    const { result: { rows } } = await api('/edit-forms/objects/search', {
      asTreeselect: true,
      formType: props.formType,
      search: searchQuery,
    });
    callback(
      null,
      rows,
    );
  }
};

const initiatorBase = computed(() => `${props.formType}-${props.context?.label}`);
const initiatorEdit = computed(() => `${initiatorBase.value}-${model.value}-edit`);
const initiatorAdd = computed(() => `${initiatorBase.value}-add`);

watch(initiator, () => {
  if (initiatorHasRead.value) {
    return;
  }
  if (initiator.value === initiatorAdd.value && editPrevEditId.value) {
    model.value = editPrevEditId.value;
  }
  initiatorHasRead.value = true;
}, {
  immediate: true,
});

const edit = () => {
  store.dispatch(EDIT_OPEN, {
    formType: props.formType,
    editId: model.value,
    initiator: initiatorEdit.value,
  });
};

const add = () => {
  store.dispatch(EDIT_OPEN, {
    formType: props.formType,
    editId: null,
    initiator: initiatorAdd.value,
  });
};
</script>

<style lang="scss" module>
.container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 5px;
}
</style>
