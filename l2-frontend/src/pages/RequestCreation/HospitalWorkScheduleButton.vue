<template>
  <span class="navbar-brand org-title">
    <button
      type="button"
      class="hospital-work-schedule-btn"
      @click="openModal"
    >
      Организация: {{ title }}
    </button>
    <Modal
      v-if="isOpen"
      show-footer="true"
      white-bg="true"
      width="480px"
      @close="closeModal"
    >
      <span slot="header">Режим работы</span>
      <div slot="body">
        <div
          v-if="isLoading"
          class="schedule-loading"
        >
          Загрузка...
        </div>
        <div
          v-else
          class="schedule-days"
        >
          <div
            v-for="day in days"
            :key="day.id"
            class="schedule-day"
          >
            <div class="schedule-day-title">
              {{ day.title }}
            </div>
            <label class="schedule-time">
              <span>с</span>
              <input
                v-model="schedule[day.id].from"
                type="time"
                class="form-control"
              >
            </label>
            <label class="schedule-time">
              <span>по</span>
              <input
                v-model="schedule[day.id].to"
                type="time"
                class="form-control"
              >
            </label>
          </div>
        </div>
      </div>
      <div slot="footer">
        <div class="schedule-footer">
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="closeModal"
          >
            Закрыть
          </button>
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            :disabled="isLoading || isSaving"
            @click="save"
          >
            {{ isSaving ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </Modal>
  </span>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import api from '@/api';
import useNotify from '@/hooks/useNotify';
import Modal from '@/ui-cards/Modal.vue';

defineProps<{
  title: string;
}>();

const days = [
  { id: 'mon', title: 'Понедельник' },
  { id: 'tue', title: 'Вторник' },
  { id: 'wed', title: 'Среда' },
  { id: 'thu', title: 'Четверг' },
  { id: 'fri', title: 'Пятница' },
  { id: 'sat', title: 'Суббота' },
  { id: 'sun', title: 'Воскресенье' },
] as const;

type DayId = typeof days[number]['id'];
type DayHours = { from: string; to: string };

const notify = useNotify();
const isOpen = ref(false);
const isLoading = ref(false);
const isSaving = ref(false);

const emptySchedule = (): Record<DayId, DayHours> => ({
  mon: { from: '', to: '' },
  tue: { from: '', to: '' },
  wed: { from: '', to: '' },
  thu: { from: '', to: '' },
  fri: { from: '', to: '' },
  sat: { from: '', to: '' },
  sun: { from: '', to: '' },
});

const schedule = ref<Record<DayId, DayHours>>(emptySchedule());

const clock = (value: unknown) => {
  const text = String(value || '').trim();
  return text.length >= 5 && text[2] === ':' ? text.slice(0, 5) : text;
};

const applySchedule = (raw: unknown) => {
  const next = emptySchedule();
  const source = raw && typeof raw === 'object' ? raw as Record<string, DayHours> : {};
  days.forEach((day) => {
    const row = source[day.id] || { from: '', to: '' };
    next[day.id] = { from: clock(row.from), to: clock(row.to) };
  });
  schedule.value = next;
};

const scheduleError = () => {
  const timeRe = /^([01]\d|2[0-3]):[0-5]\d$/;
  const invalidDay = days.find((day) => {
    const row = schedule.value[day.id];
    const start = clock(row.from);
    const end = clock(row.to);
    if (!start && !end) {
      return false;
    }
    return !timeRe.test(start) || !timeRe.test(end) || end <= start;
  });
  if (!invalidDay) {
    return '';
  }
  const row = schedule.value[invalidDay.id];
  const start = clock(row.from);
  const end = clock(row.to);
  if (!timeRe.test(start) || !timeRe.test(end)) {
    return `${invalidDay.title}: укажите время с и по`;
  }
  return `${invalidDay.title}: время «по» должно быть позже «с»`;
};

const openModal = async () => {
  isOpen.value = true;
  isLoading.value = true;
  try {
    const { ok, message, schedule: saved } = await api('requests/work-schedule');
    if (!ok) {
      notify.error(message || 'Не удалось загрузить режим работы');
      isOpen.value = false;
      return;
    }
    applySchedule(saved);
  } catch {
    notify.error('Не удалось загрузить режим работы');
    isOpen.value = false;
  } finally {
    isLoading.value = false;
  }
};

const closeModal = () => {
  if (isSaving.value) {
    return;
  }
  isOpen.value = false;
};

const save = async () => {
  const error = scheduleError();
  if (error) {
    notify.error(error);
    return;
  }
  isSaving.value = true;
  try {
    const { ok, message, schedule: saved } = await api('requests/work-schedule/save', {
      schedule: schedule.value,
    });
    if (!ok) {
      notify.error(message || 'Не удалось сохранить режим работы');
      return;
    }
    applySchedule(saved);
    notify.ok(message || 'Режим работы сохранён');
    isOpen.value = false;
  } catch {
    notify.error('Не удалось сохранить режим работы');
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.hospital-work-schedule-btn {
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: #fff;
  font: inherit;
  line-height: inherit;
  cursor: pointer;
}

.hospital-work-schedule-btn:hover,
.hospital-work-schedule-btn:focus {
  color: #fff;
  background: transparent;
  text-decoration: underline;
  outline: none;
}

.schedule-loading {
  padding: 12px 0;
}

.schedule-days {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.schedule-day {
  display: flex;
  align-items: center;
  gap: 12px;
}

.schedule-day-title {
  width: 130px;
  flex: 0 0 130px;
  color: #000;
}

.schedule-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}

.schedule-footer .btn {
  width: auto !important;
  flex: 0 0 auto;
}

.schedule-time {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-weight: normal;
}

.schedule-time .form-control {
  width: 118px;
  height: 34px;
}
</style>
