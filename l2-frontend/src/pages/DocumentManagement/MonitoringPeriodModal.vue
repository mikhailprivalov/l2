<template>
  <Modal
    v-if="open"
    show-footer="true"
    white-bg="true"
    min-width="90%"
    overflow-unset="true"
    results-editor
    @close="close"
  >
    <span slot="header">Настройка назначений</span>
    <div
      slot="body"
      class="period-body"
    >
      <div
        v-if="loadError"
        class="period-missing"
      >
        {{ loadError }}
      </div>
      <div
        v-else-if="missing.length"
        class="period-missing"
      >
        Не заполнены: {{ missing.join('; ') }}
      </div>
      <DescriptiveForm
        v-if="research"
        :research="research"
        :patient="patient"
        :confirmed="false"
      />
    </div>
    <div
      slot="footer"
      class="period-footer"
    >
      <button
        type="button"
        class="btn btn-blue-nb"
        @click="close"
      >
        Закрыть
      </button>
      <button
        type="button"
        class="btn btn-blue-nb"
        :disabled="!canConfirm"
        @click="confirm"
      >
        Создать
      </button>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import api from '@/api';
import { vField, vGroup } from '@/components/visibility-triggers';
import DescriptiveForm from '@/forms/DescriptiveForm.vue';
import Modal from '@/ui-cards/Modal.vue';

const props = defineProps<{
  open: boolean;
  directionParamsId: number;
}>();

const emit = defineEmits<{
  close: [];
  confirm: [params: Record<string, unknown>];
}>();

const patient = {};
const research = ref<Record<string, any> | null>(null);
const loadError = ref('');

const fieldEmpty = (field: { value?: unknown; field_type?: number }) => {
  const { value, field_type: fieldType } = field;
  if (value === '' || value === '- Не выбрано' || !value) {
    return true;
  }
  if (fieldType !== 29) {
    return false;
  }
  const text = String(value);
  return text.includes('"address": ""') || text.includes('"address":""');
};

const missing = computed(() => {
  const form = research.value;
  if (!form?.groups) {
    return [];
  }
  const labels: string[] = [];
  for (const group of form.groups) {
    if (!vGroup(group, form.groups, patient)) {
      continue;
    }
    let index = 0;
    for (const field of group.fields || []) {
      index += 1;
      if (field.required && fieldEmpty(field) && vField(group, form.groups, field.visibility, patient)) {
        const title = field.title === '' ? `поле ${index}` : field.title;
        labels.push(`${group.title ? `${group.title} ` : ''}${title}`);
      }
    }
  }
  return labels.slice(0, 2);
});

const canConfirm = computed(() => Boolean(research.value?.groups?.length) && missing.value.length === 0);

const close = () => {
  emit('close');
};

const confirm = () => {
  if (!canConfirm.value || !research.value) {
    return;
  }
  emit('confirm', JSON.parse(JSON.stringify(research.value)));
};

const load = async (id: number) => {
  research.value = null;
  loadError.value = '';
  try {
    const data = await api('researches/get-direction-params', { pk: id });
    if (!props.open || props.directionParamsId !== id) {
      return;
    }
    if (!data?.groups?.length) {
      loadError.value = 'У мониторинга не заданы параметры';
      return;
    }
    data.show = true;
    research.value = data;
  } catch {
    if (props.open && props.directionParamsId === id) {
      loadError.value = 'Не удалось загрузить параметры';
    }
  }
};

watch(
  () => [props.open, props.directionParamsId] as const,
  ([isOpen, id]) => {
    if (!isOpen || !id) {
      research.value = null;
      return;
    }
    load(id);
  },
);
</script>

<style scoped lang="scss">
.period-body {
  min-width: 500px;
}

.period-missing {
  margin-bottom: 8px;
}

.period-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;

  .btn {
    width: auto !important;
  }
}
</style>
