<template>
  <div class="board-page">
    <div class="toolbar panel panel-default panel-flt">
      <div class="panel-body">
        <div class="row">
          <div class="col-xs-3">
            <div class="input-group treeselect-noborder-left">
              <span class="input-group-addon">Подразделение</span>
              <Treeselect
                v-model="departmentPk"
                :options="departments"
                :multiple="false"
                :disable-branch-nodes="true"
                :clearable="false"
                :append-to-body="true"
                class="treeselect-wide"
              />
            </div>
          </div>
          <div class="col-xs-3">
            <div class="mode-switch">
              <button
                class="btn btn-default"
                :class="{ active: viewMode === 'day' }"
                @click="viewMode = 'day'"
              >
                День
              </button>
              <button
                class="btn btn-default"
                :class="{ active: viewMode === 'week' }"
                @click="viewMode = 'week'"
              >
                Неделя
              </button>
              <button
                class="btn btn-default"
                :class="{ active: viewMode === 'month' }"
                @click="viewMode = 'month'"
              >
                Месяц
              </button>
            </div>
          </div>
          <div class="col-xs-3 text-right">
            <div class="btn-group">
              <button
                class="btn btn-default"
                @click="navigate(-1)"
              >
                ←
              </button>
              <button
                class="btn btn-default"
                @click="goToday"
              >
                Сегодня
              </button>
              <button
                class="btn btn-default"
                @click="navigate(1)"
              >
                →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="calendar-wrap">
      <div class="doctor-badges">
        <button
          type="button"
          class="badge badge-secondary doctor-badge-btn"
          :class="{ active: doctorPk === -1 }"
          @click="doctorPk = -1"
        >
          Все врачи
        </button>
        <button
          v-for="doctor in doctors"
          :key="doctor.pk"
          type="button"
          draggable="true"
          class="badge badge-secondary doctor-badge-btn doctor-badge-draggable"
          :class="{ active: doctorPk === doctor.pk }"
          @click="doctorPk = doctor.pk"
          @dragstart="onDoctorDragStart($event, doctor.pk)"
          @dragend="onDoctorDragEnd"
        >
          {{ doctor.fio }}
        </button>
      </div>
      <table class="table table-bordered table-condensed calendar-table">
        <thead>
          <tr>
            <th class="sticky-col chamber-col">
              Палата
            </th>
            <th class="sticky-col bed-col">
              Койка
            </th>
            <th
              v-for="day in visibleDays"
              :key="day.key"
              class="day-col"
            >
              {{ day.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-for="row in chamberRows">
            <tr
              v-for="(bed, bedIdx) in row.beds"
              :key="`${row.pk}-${bed.pk}`"
            >
              <td
                v-if="bedIdx === 0"
                :rowspan="row.beds.length || 1"
                class="sticky-col chamber-col chamber-cell"
              >
                {{ row.label }}
              </td>
              <td class="sticky-col bed-col bed-cell">
                {{ bed.bed_number }}
              </td>
              <td
                v-for="day in visibleDays"
                :key="`${bed.pk}-${day.key}`"
                class="day-cell"
                :class="{ 'day-cell--drop-hover': dragOverCellKey === cellKey(bed.pk, day.key) }"
                @click="openEditModal(bed.pk, day.key)"
                @dragover.prevent="onCellDragOver(bed.pk, day.key)"
                @dragleave="onCellDragLeave($event, bed.pk, day.key)"
                @drop.prevent="onCellDrop($event, bed.pk, day.key)"
              >
                <div
                  v-for="rec in cellRecordList(bed.pk, day.key)"
                  :key="`${bed.pk}-${day.key}-${rec.pk}`"
                  class="record record--draggable"
                  draggable="true"
                  :title="rec.patient_fio"
                  @dragstart.stop="onPatientDragStart($event, rec)"
                  @dragend="onPatientDragEnd"
                >
                  <div class="record-line record-line--patient">
                    <span class="record-patient">
                      <template v-if="surnameFromFio(rec.patient_fio)">
                        <span
                          class="record-patient-surname"
                          :class="genderColorClass(rec.patient_sex)"
                        >{{ surnameFromFio(rec.patient_fio) }}</span><span
                          v-if="cellPatientAgePart(rec)"
                          class="record-patient-age"
                        > - {{ cellPatientAgePart(rec) }}</span>
                      </template>
                      <span
                        v-else
                        class="record-sex--muted"
                      >—</span>
                    </span>
                    <span class="record-line-actions">
                      <span
                        v-if="accompanyingDisplayLetter(rec)"
                        class="record-accompany-letter"
                        :class="genderColorClass(rec.accompanyng_child_sex)"
                        :title="accompanyingLetterTitle(rec)"
                      >{{ accompanyingDisplayLetter(rec) }}</span>
                    </span>
                  </div>
                  <div class="record-rule" />
                  <div class="record-line record-line--doctor">
                    {{ formatCellDoctorSurname(rec) || '\u00a0' }}
                  </div>
                </div>
              </td>
            </tr>
          </template>
          <tr v-if="chamberRows.length === 0">
            <td
              colspan="100"
              class="text-center"
            >
              Нет палат или данных за выбранный период
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="isEditModalOpen"
      class="edit-modal-overlay"
      @click.self="closeEditModal"
    >
      <div class="edit-modal panel panel-default">
        <div class="panel-heading">
          Редактирование госпитализации
          <button
            type="button"
            class="close"
            @click="closeEditModal"
          >
            <span>&times;</span>
          </button>
        </div>
        <div class="panel-body">
          <div class="form-group">
            <label>ФИО пациента</label>
            <input
              v-model.trim="editingForm.patientFioText"
              class="form-control"
              type="text"
              placeholder="ФИО"
            >
          </div>
          <div class="form-group">
            <label>Номер направления (direction_id)</label>
            <input
              v-model.trim="editingForm.directionIdText"
              class="form-control"
              type="text"
              inputmode="numeric"
              placeholder="необязательно"
            >
            <p class="help-block small text-muted">
              Вручную. Пустое поле — без привязки к направлению.
            </p>
          </div>
          <div
            v-if="editingRecordPk"
            class="form-group modal-doctor-field"
          >
            <label>Лечащий врач</label>
            <div class="modal-doctor-row">
              <span
                v-if="editingForm.doctorFio"
                class="modal-doctor-name"
              >{{ editingForm.doctorFio }}</span>
              <span
                v-else
                class="text-muted modal-doctor-empty"
              >не назначен</span>
              <button
                v-if="editingForm.doctorPk != null"
                type="button"
                class="btn btn-default btn-sm modal-doctor-clear"
                @click="clearModalDoctor"
              >
                Снять
              </button>
            </div>
          </div>
          <div class="form-group">
            <label>Пол</label>
            <div class="btn-group">
              <button
                type="button"
                class="btn btn-default gender-btn"
                :class="{ active: editingForm.patientSex === 'м' }"
                @click="editingForm.patientSex = 'м'"
              >
                М
              </button>
              <button
                type="button"
                class="btn btn-default gender-btn"
                :class="{ active: editingForm.patientSex === 'ж' }"
                @click="editingForm.patientSex = 'ж'"
              >
                Ж
              </button>
            </div>
          </div>
          <div class="row">
            <div class="col-xs-6 form-group">
              <label>Дата рождения</label>
              <input
                v-model="editingForm.birthday"
                class="form-control"
                type="date"
              >
            </div>
            <div class="col-xs-6 form-group">
              <label>Возраст</label>
              <input
                v-model.trim="editingForm.patientAgeText"
                class="form-control"
                type="text"
                maxlength="3"
              >
            </div>
          </div>
          <div class="form-group">
            <label>Сопровождающий ребёнка</label>
            <div class="treeselect-noborder-left edit-modal-treeselect">
              <Treeselect
                :value="editingForm.accompanyngChildType"
                :options="accompanyingChildOptions"
                :multiple="false"
                :clearable="true"
                :append-to-body="true"
                :z-index="10050"
                class="treeselect-wide"
                placeholder="Не указано"
                @input="setAccompanyngChildType"
              />
            </div>
          </div>
          <div class="row">
            <div class="col-xs-6 form-group">
              <label>Дата начала</label>
              <input
                v-model="editingForm.planDateIn"
                class="form-control"
                type="date"
              >
            </div>
            <div class="col-xs-6 form-group">
              <label>Дата окончания</label>
              <input
                v-model="editingForm.planDateOut"
                class="form-control"
                type="date"
              >
            </div>
          </div>
        </div>
        <div class="panel-footer modal-actions">
          <button
            class="btn btn-primary"
            @click="saveEditingCell"
          >
            Сохранить
          </button>
          <button
            v-if="editingRecordPk"
            type="button"
            class="btn btn-warning"
            title="Полностью удаляет запись PatientToBed из базы для этой госпитализации"
            @click="clearBedFromModal"
          >
            Освободить койку
          </button>
          <button
            class="btn btn-default"
            @click="closeEditModal"
          >
            Отмена
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import moment from 'moment';
import Treeselect from '@riophae/vue-treeselect';
import {
  computed,
  getCurrentInstance,
  onMounted,
  ref,
  watch,
} from 'vue';

import api from '@/api';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

type ViewMode = 'day' | 'week' | 'month'

interface DepartmentOption {
  id: number;
  label: string;
}

interface BedData {
  pk: number;
  bed_number: number;
}

interface ChamberData {
  pk: number;
  label: string;
  beds: BedData[];
}

interface AccompanyingChildOption {
  id: string;
  label: string;
}

interface CalendarRecord {
  pk: number;
  bed_pk: number;
  doctor_pk: number | null;
  doctor_fio?: string;
  patient_fio: string;
  patient_sex: string;
  birthday: string | null;
  patient_age_text: string;
  direction_pk: number | null;
  date_in: string | null;
  date_out: string | null;
  plan_date_in: string | null;
  plan_date_out: string | null;
  accompanyng_child_type?: string;
  accompanyng_child_sex?: string;
}

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const departments = ref<DepartmentOption[]>([]);
const departmentPk = ref<number | null>(null);
const doctorPk = ref<number>(-1);
const doctors = ref<any[]>([]);
const accompanyingChildOptions = ref<AccompanyingChildOption[]>([]);
const chambers = ref<ChamberData[]>([]);
const records = ref<CalendarRecord[]>([]);
const viewMode = ref<ViewMode>('week');
const anchorDate = ref(moment());
const isEditModalOpen = ref(false);
const editingBedPk = ref<number | null>(null);
const editingDayKey = ref('');
const editingRecordPk = ref<number | null>(null);
const editingForm = ref({
  patientFioText: '',
  directionIdText: '',
  patientSex: 'м',
  birthday: '',
  patientAgeText: '',
  planDateIn: '',
  planDateOut: '',
  doctorPk: null as number | null,
  doctorFio: '',
  accompanyngChildType: null as string | null,
});

const dragOverCellKey = ref('');
const suppressCellClick = ref(false);

const visibleDays = computed(() => {
  let start = anchorDate.value.clone();
  let end = anchorDate.value.clone();
  if (viewMode.value === 'day') {
    start = anchorDate.value.clone().startOf('day');
    end = anchorDate.value.clone().endOf('day');
  }
  if (viewMode.value === 'week') {
    start = anchorDate.value.clone().startOf('isoWeek');
    end = anchorDate.value.clone().endOf('isoWeek');
  }
  if (viewMode.value === 'month') {
    start = anchorDate.value.clone().startOf('month');
    end = anchorDate.value.clone().endOf('month');
  }
  const days: Array<{ key: string, label: string }> = [];
  const cursor = start.clone();
  while (cursor.isSameOrBefore(end, 'day')) {
    days.push({
      key: cursor.format('YYYY-MM-DD'),
      label: cursor.format('DD.MM'),
    });
    cursor.add(1, 'day');
  }
  return days;
});

const chamberRows = computed(() => chambers.value.map((row) => {
  const seenPk = new Set<number>();
  const beds = (row.beds || []).filter((b) => {
    if (seenPk.has(b.pk)) {
      return false;
    }
    seenPk.add(b.pk);
    return true;
  });
  return { ...row, beds };
}));

const isDayInRecordSpan = (rec: CalendarRecord, dayKey: string) => {
  const start = moment(rec.plan_date_in || rec.date_in);
  const d = moment(dayKey, 'YYYY-MM-DD');
  if (!start.isValid() || !d.isValid() || d.isBefore(start, 'day')) {
    return false;
  }
  const endParts = [rec.plan_date_out, rec.date_out].filter(Boolean) as string[];
  if (!endParts.length) {
    return true;
  }
  const endMoments = endParts.map((x) => moment(x)).filter((m) => m.isValid());
  if (!endMoments.length) {
    return true;
  }
  const end = moment.min(endMoments);
  return !d.isAfter(end, 'day');
};

const recordByBedAndDay = computed(() => {
  const map = new Map<string, CalendarRecord>();
  const days = visibleDays.value;
  if (!days.length) {
    return map;
  }
  for (const record of records.value) {
    const start = moment(record.plan_date_in || record.date_in);
    if (!start.isValid()) {
      continue;
    }
    for (const { key: dayKey } of days) {
      if (!isDayInRecordSpan(record, dayKey)) {
        continue;
      }
      map.set(`${record.bed_pk}-${dayKey}`, record);
    }
  }
  return map;
});

const getRecordForDay = (bedPk: number, dayKey: string) => recordByBedAndDay.value.get(`${bedPk}-${dayKey}`);

const surnameFromFio = (fio: string | null | undefined) => {
  const s = (fio || '').trim();
  if (!s) {
    return '';
  }
  return s.split(/\s+/)[0] || '';
};

const cellPatientAgePart = (record: CalendarRecord) => {
  const fromText = (record.patient_age_text || '').trim();
  if (fromText) {
    return fromText;
  }
  if (record.birthday) {
    const y = moment().diff(moment(record.birthday, 'YYYY-MM-DD'), 'years');
    if (Number.isFinite(y) && y >= 0) {
      return String(y);
    }
  }
  return '';
};

const formatCellDoctorSurname = (record: CalendarRecord) => surnameFromFio(record.doctor_fio);

const cellRecordList = (bedPk: number, dayKey: string): CalendarRecord[] => {
  const r = getRecordForDay(bedPk, dayKey);
  return r ? [r] : [];
};

const accompanyingDisplayLetter = (record: CalendarRecord) => {
  const t = (record.accompanyng_child_type || '').trim();
  if (!t) {
    return '';
  }
  return t.charAt(0).toLocaleUpperCase('ru-RU');
};

const genderColorClass = (sexRaw: string | null | undefined) => {
  const sex = (sexRaw || '').trim();
  if (!sex || sex === '-') {
    return 'record-sex--muted';
  }
  const c = sex.charAt(0);
  const cp = c.codePointAt(0) ?? 0;
  if (cp === 0x0416 || cp === 0x0436) {
    return 'record-sex--female';
  }
  if (cp === 0x041c || cp === 0x043c) {
    return 'record-sex--male';
  }
  if (c === 'M' || c === 'm') {
    return 'record-sex--male';
  }
  if (c === 'F' || c === 'f') {
    return 'record-sex--female';
  }
  return 'record-sex--muted';
};

const accompanyingLetterTitle = (record: CalendarRecord) => {
  const t = (record.accompanyng_child_type || '').trim();
  const s = (record.accompanyng_child_sex || '').trim();
  if (!t) {
    return '';
  }
  return s ? `${t}, пол сопровождающего: ${s}` : t;
};

const goToday = () => {
  anchorDate.value = moment();
};

const navigate = (direction: number) => {
  if (viewMode.value === 'day') {
    anchorDate.value = anchorDate.value.clone().add(direction, 'day');
  } else if (viewMode.value === 'week') {
    anchorDate.value = anchorDate.value.clone().add(direction, 'week');
  } else {
    anchorDate.value = anchorDate.value.clone().add(direction, 'month');
  }
};

const loadDepartments = async () => {
  const { data } = await api('procedural-list/suitable-departments');
  departments.value = data;
};

const loadAccompanyingChildOptions = async () => {
  const res = await api('chambers/get-accompanying-child-options');
  const list = res?.data;
  accompanyingChildOptions.value = Array.isArray(list) ? list : [];
};

const loadDoctors = async () => {
  if (!departmentPk.value) {
    doctors.value = [];
    return;
  }
  const response = await api('chambers/get-attending-doctors', {
    department_pk: departmentPk.value,
    only_stationar_role: true,
  });
  doctors.value = response.data || [];
};

const loadCalendar = async () => {
  if (!departmentPk.value || visibleDays.value.length === 0) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const start = visibleDays.value[0].key;
  const end = visibleDays.value[visibleDays.value.length - 1].key;
  const response = await api('chambers/get-hospitalization-calendar', {
    department_pk: departmentPk.value,
    doctor_pk: doctorPk.value > 0 ? doctorPk.value : null,
    start_date: start,
    end_date: end,
  });
  chambers.value = response?.data?.chambers || [];
  records.value = response?.data?.records || [];
  await store.dispatch(actions.DEC_LOADING);
};

const cellKey = (bedPk: number, dayKey: string) => `${bedPk}-${dayKey}`;

const onDoctorDragStart = (e: DragEvent, doctorPkInner: number) => {
  e.dataTransfer?.setData('application/x-l2-doctor-pk', String(doctorPkInner));
  e.dataTransfer?.setData('text/plain', String(doctorPkInner));
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'copy';
  }
};

const onDoctorDragEnd = () => {
  dragOverCellKey.value = '';
};

const onPatientDragStart = (e: DragEvent, rec: CalendarRecord) => {
  e.stopPropagation();
  e.dataTransfer?.setData('application/x-l2-hospitalization-move', String(rec.pk));
  e.dataTransfer?.setData('text/plain', `hosp-move:${rec.pk}`);
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
  }
};

const onPatientDragEnd = () => {
  dragOverCellKey.value = '';
  suppressCellClick.value = true;
  window.setTimeout(() => {
    suppressCellClick.value = false;
  }, 200);
};

const onCellDragOver = (bedPk: number, dayKey: string) => {
  dragOverCellKey.value = cellKey(bedPk, dayKey);
};

const onCellDragLeave = (e: DragEvent, bedPk: number, dayKey: string) => {
  const current = e.currentTarget as Node | null;
  const related = e.relatedTarget as Node | null;
  if (current && related && current.contains(related)) {
    return;
  }
  if (dragOverCellKey.value === cellKey(bedPk, dayKey)) {
    dragOverCellKey.value = '';
  }
};

const onPatientBedDrop = async (targetBedPk: number, targetDayKey: string, recordPkRaw: string) => {
  const recordPk = Number.parseInt(recordPkRaw, 10);
  if (Number.isNaN(recordPk) || !departmentPk.value) {
    return;
  }
  const sourceRec = records.value.find((r) => r.pk === recordPk);
  if (!sourceRec) {
    root.$emit('msg', 'error', 'Запись не найдена');
    return;
  }
  if (!isDayInRecordSpan(sourceRec, targetDayKey)) {
    root.$emit('msg', 'error', 'Нельзя перенести на дату вне периода госпитализации');
    return;
  }
  if (sourceRec.bed_pk === targetBedPk) {
    root.$emit('msg', 'error', 'Выберите другую койку');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('chambers/move-hospitalization-to-bed', {
    department_pk: departmentPk.value,
    record_pk: recordPk,
    target_bed_id: targetBedPk,
    move_from_date: targetDayKey,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Пациент перенесён');
    await loadCalendar();
  } else {
    root.$emit('msg', 'error', message || 'Не удалось перенести пациента');
  }
};

const onCellDrop = async (e: DragEvent, bedPk: number, dayKey: string) => {
  dragOverCellKey.value = '';
  const hospMove = e.dataTransfer?.getData('application/x-l2-hospitalization-move');
  if (hospMove) {
    await onPatientBedDrop(bedPk, dayKey, hospMove);
    return;
  }
  const docRaw = e.dataTransfer?.getData('application/x-l2-doctor-pk') || e.dataTransfer?.getData('text/plain') || '';
  if (docRaw.startsWith('hosp-move:')) {
    return;
  }
  const docPk = Number.parseInt(docRaw || '', 10);
  if (!docRaw || Number.isNaN(docPk)) {
    return;
  }
  const record = getRecordForDay(bedPk, dayKey);
  if (!record?.pk) {
    root.$emit('msg', 'error', 'В этой ячейке нет госпитализации — назначить врача некуда');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('chambers/update-hospitalization-record', {
    record_pk: record.pk,
    doctor_id: docPk,
    patient_fio_text: record.patient_fio || '',
    patient_sex: record.patient_sex || 'м',
    birthday: record.birthday || null,
    patient_age_text: record.patient_age_text || '',
    plan_date_in: record.plan_date_in || record.date_in || null,
    plan_date_out: record.plan_date_out || record.date_out || null,
    accompanyng_child_type: record.accompanyng_child_type || '',
    direction_id: record.direction_pk ?? null,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Врач назначен');
    await loadCalendar();
  } else {
    root.$emit('msg', 'error', message || 'Не удалось назначить врача');
  }
};

const closeEditModal = () => {
  isEditModalOpen.value = false;
  editingBedPk.value = null;
  editingDayKey.value = '';
  editingRecordPk.value = null;
};

const openEditModal = (bedPk: number, dayKey: string) => {
  if (suppressCellClick.value) {
    return;
  }
  const record = getRecordForDay(bedPk, dayKey);
  editingBedPk.value = bedPk;
  editingDayKey.value = dayKey;
  editingRecordPk.value = record?.pk || null;
  editingForm.value = {
    patientFioText: record?.patient_fio || '',
    directionIdText: record?.direction_pk != null && record.direction_pk > 0 ? String(record.direction_pk) : '',
    patientSex: record?.patient_sex || 'м',
    birthday: record?.birthday || '',
    patientAgeText: record?.patient_age_text || '',
    planDateIn: record?.plan_date_in || record?.date_in || dayKey,
    planDateOut: record?.plan_date_out || record?.date_out || dayKey,
    doctorPk: record?.doctor_pk ?? null,
    doctorFio: (record?.doctor_fio || '').trim(),
    accompanyngChildType: (record?.accompanyng_child_type && String(record.accompanyng_child_type).trim()) || null,
  };
  isEditModalOpen.value = true;
};

const clearModalDoctor = () => {
  editingForm.value.doctorPk = null;
  editingForm.value.doctorFio = '';
};

const setAccompanyngChildType = (value: string | null | undefined) => {
  editingForm.value = {
    ...editingForm.value,
    accompanyngChildType: value ?? null,
  };
};

const saveEditingCell = async () => {
  if (!departmentPk.value || !editingBedPk.value) {
    return;
  }
  if (!editingForm.value.patientFioText) {
    root.$emit('msg', 'error', 'Заполните ФИО пациента');
    return;
  }
  const dirTrim = editingForm.value.directionIdText.trim();
  let directionIdPayload: number | null = null;
  if (dirTrim) {
    const n = Number.parseInt(dirTrim, 10);
    if (Number.isNaN(n) || n <= 0) {
      root.$emit('msg', 'error', 'Номер направления: укажите положительное целое число или оставьте поле пустым');
      return;
    }
    directionIdPayload = n;
  }
  await store.dispatch(actions.INC_LOADING);
  let result;
  if (editingRecordPk.value) {
    result = await api('chambers/update-hospitalization-record', {
      record_pk: editingRecordPk.value,
      doctor_id: editingForm.value.doctorPk,
      direction_id: directionIdPayload,
      patient_fio_text: editingForm.value.patientFioText,
      patient_sex: editingForm.value.patientSex,
      birthday: editingForm.value.birthday || null,
      patient_age_text: editingForm.value.patientAgeText,
      plan_date_in: editingForm.value.planDateIn,
      plan_date_out: editingForm.value.planDateOut,
      accompanyng_child_type: editingForm.value.accompanyngChildType || '',
    });
  } else {
    result = await api('chambers/save-hospitalization-by-fio', {
      department_pk: departmentPk.value,
      bed_id: editingBedPk.value,
      doctor_id: editingForm.value.doctorPk,
      direction_id: directionIdPayload,
      patient_fio_text: editingForm.value.patientFioText,
      patient_sex: editingForm.value.patientSex,
      birthday: editingForm.value.birthday || null,
      patient_age_text: editingForm.value.patientAgeText,
      plan_date_in: editingForm.value.planDateIn,
      plan_date_out: editingForm.value.planDateOut,
      accompanyng_child_type: editingForm.value.accompanyngChildType || '',
    });
  }
  await store.dispatch(actions.DEC_LOADING);
  if (result?.ok) {
    root.$emit('msg', 'ok', 'Данные сохранены');
    closeEditModal();
    await loadCalendar();
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось сохранить запись');
  }
};

const clearBedFromModal = async () => {
  if (!editingRecordPk.value) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const result = await api('chambers/clear-patient-from-bed', {
    record_pk: editingRecordPk.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (result?.ok) {
    root.$emit('msg', 'ok', 'Запись удалена');
    closeEditModal();
    records.value = [];
    await loadCalendar();
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось освободить койку');
  }
};

watch([departmentPk, viewMode, anchorDate, doctorPk], async () => {
  await loadCalendar();
});

watch(departmentPk, async () => {
  await loadDoctors();
  doctorPk.value = -1;
});

onMounted(async () => {
  await Promise.all([loadDepartments(), loadAccompanyingChildOptions()]);
});
</script>

<style scoped lang="scss">
.board-page {
  padding: 10px 16px;
}

.toolbar {
  margin-bottom: 8px;
}

.mode-switch {
  display: flex;
  gap: 4px;
}

.mode-switch .active {
  background: #049372;
  color: #fff;
}

.calendar-wrap {
  overflow: auto;
  max-height: calc(100vh - 220px);
}

.doctor-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0 0 8px;
}

.doctor-badge-btn {
  border: none;
  line-height: 1.2;
  cursor: pointer;
}

.doctor-badge-btn.active {
  background: #049372;
}

.doctor-badge-draggable {
  cursor: grab;
}

.doctor-badge-draggable:active {
  cursor: grabbing;
}

.calendar-table {
  table-layout: fixed;
  min-width: 1100px;
}

.chamber-col {
  width: 96px;
}

.bed-col {
  width: 70px;
}

.day-col {
  width: 96px;
  text-align: center;
}

.sticky-col {
  position: sticky;
  background: #fff;
  z-index: 3;
}

.chamber-col.sticky-col {
  left: 0;
}

.bed-col.sticky-col {
  left: 96px;
}

.chamber-cell {
  font-weight: 600;
}

.bed-cell {
  text-align: center;
}

.day-cell {
  min-height: 44px;
  height: auto;
  vertical-align: top;
  padding: 3px 4px;
  cursor: pointer;
}

.day-cell--drop-hover {
  box-shadow: inset 0 0 0 2px #049372;
  background: rgba(4, 147, 114, 0.12);
}

.record {
  background: transparent;
  color: inherit;
  font-size: 11px;
  line-height: 1.25;
  text-align: left;
}

.record--draggable {
  cursor: grab;
}

.record--draggable:active {
  cursor: grabbing;
}

.record-line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 4px;
  min-width: 0;
}

.record-line--patient {
  font-weight: 600;
}

.record-patient {
  display: flex;
  min-width: 0;
  align-items: baseline;
  overflow: hidden;
}

.record-patient-surname {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
}

.record-patient-age {
  flex-shrink: 0;
  font-weight: 600;
  color: #333;
}

.record-rule {
  margin: 2px 0 1px;
  border-top: 1px solid #bbb;
}

.record-line--doctor {
  font-weight: 500;
  color: #555;
  font-size: 10px;
  min-height: 1.1em;
}

.record-line-actions {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.record-accompany-letter {
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  user-select: none;
}

.record-sex--male {
  color: #0d47a1;
}

.record-sex--female {
  color: #c62828;
}

.record-sex--muted {
  color: #757575;
}

.modal-actions {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
}

.modal-actions .btn-primary {
  background: #049372;
  border-color: #049372;
  color: #fff;
}

.modal-actions .btn-primary:hover,
.modal-actions .btn-primary:focus,
.modal-actions .btn-primary:active {
  background: #037f61;
  border-color: #037f61;
  color: #fff;
}

.gender-btn.active,
.gender-btn:hover,
.gender-btn:focus,
.gender-btn:active {
  background: #049372;
  border-color: #049372;
  color: #fff;
}

.edit-modal-overlay {
  position: fixed;
  z-index: 2000;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-modal {
  width: 560px;
  max-width: calc(100vw - 32px);
  margin: 0;
  position: relative;
  z-index: 1;
}

.edit-modal .panel-body {
  overflow: visible;
}

.edit-modal-treeselect {
  position: relative;
  z-index: 2;
}

.modal-doctor-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 30px;
}

.modal-doctor-name {
  flex: 1;
  min-width: 0;
  word-break: break-word;
}

.modal-doctor-clear {
  flex-shrink: 0;
}
</style>
