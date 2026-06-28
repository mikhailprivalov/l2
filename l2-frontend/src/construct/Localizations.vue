<template>
  <Modal
    ref="modalRef"
    show-footer="true"
    white-bg="true"
    max-width="680px"
    width="100%"
    margin-top
    margin-left-right="auto"
    @close="hideModal"
  >
    <span slot="header">Настройка локализаций ({{ title }})</span>
    <div
      v-if="loaded"
      slot="body"
      style="min-height: 200px"
    >
      <div class="list-group">
        <a
          v-for="l in localizations"
          :key="l.pk"
          href="#"
          class="list-group-item list-group-item-light"
          :class="selected[l.pk] && 'active'"
          @click.prevent="toggleSelected(l.pk)"
        >
          <input
            type="checkbox"
            :checked="!!selected[l.pk]"
          >
          {{ l.title }}
        </a>
      </div>
    </div>
    <div
      v-else
      slot="body"
      style="line-height: 200px;text-align: center"
    >
      Загрузка данных...
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-8">
          <button
            type="button"
            :disabled="!hasChanges"
            class="btn btn-primary-nb"
            @click="save"
          >
            Сохранить
          </button>
        </div>
        <div class="col-xs-4">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            @click="hideModal"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { getCurrentInstance, onMounted, ref } from 'vue';

import Modal from '@/ui-cards/Modal.vue';
import api from '@/api';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';

const props = defineProps<{
  research_pk: number;
  title: string;
}>();

const emit = defineEmits(['hide']);

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const modalRef = ref<InstanceType<typeof Modal> | null>(null);
const loaded = ref(false);
const localizations = ref<any[]>([]);
const selected = ref<Record<number, boolean>>({});
const hasChanges = ref(false);

const hideModal = () => {
  emit('hide');
  if (modalRef.value) {
    modalRef.value.$el.style.display = 'none';
  }
};

const loadData = async () => {
  await store.dispatch(actions.INC_LOADING);
  loaded.value = false;
  const { localizations: locs, selected: selectedIds } = await api('researches/localization', { pk: props.research_pk });
  localizations.value = locs;
  selected.value = locs.reduce((a: Record<number, boolean>, { pk }: { pk: number }) => ({
    ...a,
    [pk]: selectedIds.includes(pk),
  }), {});
  loaded.value = true;
  await store.dispatch(actions.DEC_LOADING);
};

const toggleSelected = (pk: number) => {
  selected.value[pk] = !selected.value[pk];
  hasChanges.value = true;
};

const save = async () => {
  await store.dispatch(actions.INC_LOADING);
  await api('researches/localization/save', {
    pk: props.research_pk,
    selected: Object.keys(selected.value).filter((pk) => selected.value[Number(pk)]),
  });
  hasChanges.value = false;
  await store.dispatch(actions.DEC_LOADING);
  root.$emit('msg', 'ok', `Локализации для исследования\n«‎${props.title}»‎\nсохранены`, 4000);
};

onMounted(() => {
  loadData();
});
</script>

<style scoped lang="scss">
.modal-mask {
  align-items: stretch !important;
  justify-content: center !important;
}

::v-deep .panel-flt {
  margin: 41px;
  align-self: stretch !important;
  width: 100%;
  display: flex;
  flex-direction: column;
}

::v-deep .panel-body {
  flex: 1;
  padding: 10px !important;
  height: calc(100% - 144px);
  min-height: 200px;
}

.list-group {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
}

.list-group-item-light {
  background-color: #f4f6f8;
  transition: all 0.2s ease-in-out;

  &.active {
    background: #049372 !important;
    border-color: #049372 !important;
  }

  input[type='checkbox'] {
    vertical-align: top;
  }
}
</style>
