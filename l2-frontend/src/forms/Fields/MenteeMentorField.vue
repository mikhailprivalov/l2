<template>
  <div class="mentee-mentor-field">
    <Treeselect
      :multiple="false"
      :disable-branch-nodes="isMentee"
      :search-nested="isMentee"
      class="treeselect-wide treeselect-34px"
      :options="options"
      :append-to-body="true"
      :clearable="true"
      :disabled="isDisabled"
      :value="selectedId"
      :z-index="5001"
      :placeholder="placeholder"
      no-results-text="Не найдено"
      no-options-text="Нет сотрудников"
      @select="onSelect"
      @input="onInput"
    />
    <div
      v-if="isMentee && selectedId"
      class="mentee-mentor-field__dates"
    >
      <div>Дата рождения: {{ dateBirth || 'не указана' }}</div>
      <div>Дата приема на работу: {{ dateEmployment || 'не указана' }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import api from '@/api';

type FieldKind = 'mentee' | 'mentor';

type Details = {
  id?: number;
  fio?: string;
  departmentId?: number;
  dateBirth?: string;
  dateEmployment?: string;
};

const props = withDefaults(defineProps<{
  value?: string;
  disabled?: boolean;
  kind?: FieldKind;
  departmentId?: number | string | null;
}>(), {
  value: '',
  disabled: false,
  kind: 'mentee',
  departmentId: null,
});

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', value: string): void;
}>();

const options = ref<any[]>([]);
const selectedId = ref<number | string | null>(null);
const details = ref<Details>({});
const ready = ref(false);

const isMentee = computed(() => props.kind === 'mentee');
const isMentor = computed(() => props.kind === 'mentor');
const dateBirth = computed(() => details.value.dateBirth || '');
const dateEmployment = computed(() => details.value.dateEmployment || '');
const hasDepartment = computed(() => props.departmentId != null && props.departmentId !== '' && Number(props.departmentId) > 0);
const isDisabled = computed(() => props.disabled || (isMentor.value && !hasDepartment.value));
const placeholder = computed(() => {
  if (isMentor.value && !hasDepartment.value) {
    return 'Сначала выберите наставляемого';
  }
  return isMentee.value ? 'Выберите наставляемого' : 'Выберите наставника';
});

function parseValue(raw?: string): Details {
  if (!raw) {
    return {};
  }
  try {
    const data = JSON.parse(raw);
    return data && typeof data === 'object' && !Array.isArray(data) ? data : {};
  } catch {
    return {};
  }
}

function applyParsed(data: Details) {
  details.value = data;
  selectedId.value = data.id ?? null;
}

function emitPayload(data: Details) {
  if (!data?.id) {
    emit('input', '');
    return;
  }
  if (isMentee.value) {
    emit('input', JSON.stringify({
      id: data.id,
      fio: data.fio || '',
      departmentId: data.departmentId,
      dateBirth: data.dateBirth || '',
      dateEmployment: data.dateEmployment || '',
    }));
    return;
  }
  emit('input', JSON.stringify({
    id: data.id,
    fio: data.fio || '',
    departmentId: data.departmentId,
  }));
}

function clear() {
  details.value = {};
  selectedId.value = null;
  emit('input', '');
}

function onSelect(node: any) {
  const raw = node.raw || node;
  const data: Details = {
    id: raw.id ?? node.id,
    fio: raw.fio || raw.label || node.label,
    departmentId: raw.departmentId,
    dateBirth: raw.dateBirth || '',
    dateEmployment: raw.dateEmployment || '',
  };
  applyParsed(data);
  emitPayload(data);
}

function onInput(value: any) {
  if (!ready.value) {
    return;
  }
  if (value == null || value === '') {
    clear();
  }
}

async function loadMentees() {
  const { result } = await api('employees/mentees');
  options.value = result || [];
}

async function loadMentors() {
  if (!hasDepartment.value) {
    options.value = [];
    return;
  }
  const { result } = await api('employees/mentors', { departmentId: Number(props.departmentId) });
  options.value = result || [];
}

watch(() => props.value, (raw) => {
  const data = parseValue(raw);
  if (data.id !== details.value.id) {
    applyParsed(data);
  } else if (!raw) {
    applyParsed({});
  }
}, { immediate: true });

watch(() => props.departmentId, async (departmentId, previousDepartmentId) => {
  if (!isMentor.value) {
    return;
  }
  await loadMentors();
  if (!hasDepartment.value) {
    if (previousDepartmentId != null && previousDepartmentId !== '' && Number(previousDepartmentId) > 0) {
      clear();
    }
    return;
  }
  if (details.value.id && details.value.departmentId != null && Number(details.value.departmentId) !== Number(departmentId)) {
    clear();
  }
});

onMounted(async () => {
  if (isMentee.value) {
    await loadMentees();
  } else if (hasDepartment.value) {
    await loadMentors();
  }
  ready.value = true;
});
</script>

<style scoped lang="scss">
.mentee-mentor-field {
  width: 100%;
}

.mentee-mentor-field__dates {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.4;
  color: #4a4a4a;
}
</style>
