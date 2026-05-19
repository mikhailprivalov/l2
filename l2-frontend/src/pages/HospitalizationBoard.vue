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
                @click="setViewMonth"
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

    <div class="board-body">
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
            {{ doctor.fio }} - {{ doctorPatientCount(doctor.pk) }}
          </button>
        </div>
        <div class="calendar-tables-stack">
          <div class="calendar-main-scroll">
            <table
              class="table table-bordered table-condensed calendar-table"
              :class="{ 'calendar-table--month': viewMode === 'month' }"
            >
              <colgroup>
                <col class="calendar-col-chamber">
                <col class="calendar-col-bed">
                <col
                  v-for="day in visibleDays"
                  :key="`col-${day.key}`"
                  class="calendar-col-day"
                >
              </colgroup>
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
                    class="day-col day-col--header"
                    :class="{
                      'day-col--today': isTodayDayColumn(day.key),
                      'day-col--hover': isDayColumnHovered(day.key),
                    }"
                    @mouseenter="onDayHeaderMouseEnter(day.key)"
                    @mouseleave="onDayHeaderMouseLeave"
                  >
                    <div class="day-col-head">
                      {{ day.label }}
                      <div class="day-col-totals">
                        <span class="day-col-totals-item">М-{{ dayColumnTotals(day.key).male }}</span>
                        <span class="day-col-totals-item">Ж-{{ dayColumnTotals(day.key).female }}</span>
                        <span class="day-col-totals-item">С-{{ dayColumnTotals(day.key).accompanying }}</span>
                      </div>
                    </div>
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
                      :class="{
                        'day-cell--drop-hover': dragOverCellKey === cellKey(bed.pk, day.key),
                        'day-cell--forbidden-edit': cellForbiddenEdit(bed.pk, day.key),
                        'day-cell--col-hover': isDayColumnHovered(day.key),
                      }"
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
                        :title="recordHoverTitle(rec, day.key)"
                        @dragstart.stop="onPatientDragStart($event, rec)"
                        @dragend="onPatientDragEnd"
                      >
                        <div class="record-line record-line--patient">
                          <span class="record-patient">
                            <span class="record-patient-name-wrap">
                              <template v-if="surnameFromFio(rec.patient_fio)">
                                <span
                                  class="record-patient-surname"
                                  :class="genderColorClass(rec.patient_sex)"
                                >
                                  <template v-if="viewMode === 'month'">
                                    {{ monthSurnameShort(rec) }}
                                  </template>
                                  <template v-else>
                                    {{ surnameFromFio(rec.patient_fio) }}
                                  </template>
                                </span><span
                                  v-if="viewMode !== 'month' && cellPatientAgePart(rec)"
                                  class="record-patient-age"
                                > - {{ cellPatientAgePart(rec) }}</span>
                              </template>
                              <span
                                v-else
                                class="record-sex--muted"
                              >—</span>
                            </span>
                          </span>
                          <span class="record-line-actions">
                            <a
                              v-if="rec.direction_pk != null && rec.direction_pk > 0"
                              :href="stationarHref(rec.direction_pk)"
                              class="record-direction-link"
                              target="_blank"
                              rel="noopener noreferrer"
                              :title="`Направление ${rec.direction_pk} (стационар)`"
                              @click.stop
                              @mousedown.stop
                            >
                              <template v-if="viewMode === 'month'">
                                {{ monthDirectionIdShort(rec.direction_pk) }}
                              </template>
                              <template v-else>
                                {{ rec.direction_pk }}
                              </template>
                            </a>
                            <span
                              v-if="accompanyingDisplayLetter(rec)"
                              class="record-accompany-letter"
                              :class="genderColorClass(rec.accompanyng_child_sex)"
                              :title="accompanyingLetterTitle(rec)"
                            >{{ accompanyingDisplayLetter(rec) }}</span>
                            <span
                              v-if="rec.is_day_hosp"
                              class="record-day-hosp-badge"
                              title="Дневной стационар"
                            >ДС</span>
                          </span>
                        </div>
                        <div class="record-line record-line--doctor">
                          <span class="record-doctor-line-inner">
                            <span class="record-doctor-name">{{ formatCellDoctorSurname(rec) || '\u00a0' }}</span><span
                              v-if="commentForRecordDay(rec, day.key).trim()"
                              class="record-comment-after-doctor"
                              :title="commentForRecordDay(rec, day.key)"
                            > · {{ cellCommentAfterDoctor(rec, day.key) }}</span>
                          </span>
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

          <div class="strip-board-block calendar-strip-block">
            <p class="strip-board-hint text-muted small">
              Дневной стационар
            </p>
            <div class="calendar-strip-scroll">
              <table
                class="table table-bordered table-condensed calendar-table calendar-table--strip"
                :class="{ 'calendar-table--month': viewMode === 'month' }"
              >
                <colgroup>
                  <col class="calendar-col-strip-sidebar">
                  <col
                    v-for="day in visibleDays"
                    :key="`strip-col-${day.key}`"
                    class="calendar-col-day"
                  >
                </colgroup>
                <thead>
                  <tr>
                    <th class="sticky-col strip-sidebar-col strip-sidebar-th">
                      Днёвники
                    </th>
                    <th
                      v-for="day in visibleDays"
                      :key="`strip-h-${day.key}`"
                      class="day-col day-col--header"
                      :class="{
                        'day-col--today': isTodayDayColumn(day.key),
                        'day-col--hover': isDayColumnHovered(day.key),
                      }"
                      @mouseenter="onDayHeaderMouseEnter(day.key)"
                      @mouseleave="onDayHeaderMouseLeave"
                    >
                      <div class="day-col-head">
                        {{ day.label }}
                        <div class="day-col-totals">
                          <span class="day-col-totals-item">М-{{ dayColumnTotals(day.key).male }}</span>
                          <span class="day-col-totals-item">Ж-{{ dayColumnTotals(day.key).female }}</span>
                          <span class="day-col-totals-item">С-{{ dayColumnTotals(day.key).accompanying }}</span>
                        </div>
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(srow, sidx) in stripRows"
                    :key="srow.rowId"
                  >
                    <td class="sticky-col strip-sidebar-col strip-sidebar-cell">
                      {{ srow.records.length ? srow.records.length : '—' }}
                    </td>
                    <td
                      v-for="day in visibleDays"
                      :key="`${srow.rowId}-${day.key}`"
                      class="day-cell"
                      :class="{'day-cell--drop-hover': dragOverStripCellKey === stripCellKey(sidx, day.key),
                               'day-cell--col-hover': isDayColumnHovered(day.key),
                      }"
                      @click="openStripCellModal(sidx, day.key)"
                      @dragover.prevent="onStripCellDragOver(sidx, day.key)"
                      @dragleave="onStripCellDragLeave($event, sidx, day.key)"
                      @drop.prevent="onStripCellDrop($event, sidx, day.key)"
                    >
                      <div
                        v-for="rec in cellStripRecordList(srow, day.key)"
                        :key="`strip-${srow.rowId}-${day.key}-${rec.pk}`"
                        class="record record--draggable"
                        draggable="true"
                        :title="recordHoverTitle(rec, day.key)"
                        @dragstart.stop="onStripPatientDragStart($event, srow, rec)"
                        @dragend="onPatientDragEnd"
                        @click.stop="openStripRecordModal(sidx, day.key, rec)"
                      >
                        <div class="record-line record-line--patient">
                          <span class="record-patient">
                            <span class="record-patient-name-wrap">
                              <template v-if="surnameFromFio(rec.patient_fio)">
                                <span
                                  class="record-patient-surname"
                                  :class="genderColorClass(rec.patient_sex)"
                                >
                                  <template v-if="viewMode === 'month'">
                                    {{ monthSurnameShort(rec) }}
                                  </template>
                                  <template v-else>
                                    {{ surnameFromFio(rec.patient_fio) }}
                                  </template>
                                </span><span
                                  v-if="viewMode !== 'month' && cellPatientAgePart(rec)"
                                  class="record-patient-age"
                                > - {{ cellPatientAgePart(rec) }}</span>
                              </template>
                              <span
                                v-else
                                class="record-sex--muted"
                              >—</span>
                            </span>
                          </span>
                          <span class="record-line-actions">
                            <a
                              v-if="rec.direction_pk != null && rec.direction_pk > 0"
                              :href="stationarHref(rec.direction_pk)"
                              class="record-direction-link"
                              target="_blank"
                              rel="noopener noreferrer"
                              :title="`Направление ${rec.direction_pk} (стационар)`"
                              @click.stop
                              @mousedown.stop
                            >
                              <template v-if="viewMode === 'month'">
                                {{ monthDirectionIdShort(rec.direction_pk) }}
                              </template>
                              <template v-else>
                                {{ rec.direction_pk }}
                              </template>
                            </a>
                            <span
                              v-if="accompanyingDisplayLetter(rec)"
                              class="record-accompany-letter"
                              :class="genderColorClass(rec.accompanyng_child_sex)"
                              :title="accompanyingLetterTitle(rec)"
                            >{{ accompanyingDisplayLetter(rec) }}</span>
                            <span
                              v-if="rec.is_day_hosp"
                              class="record-day-hosp-badge"
                              title="Дневной стационар"
                            >ДС</span>
                          </span>
                        </div>
                        <div class="record-line record-line--doctor">
                          <span class="record-doctor-line-inner">
                            <span class="record-doctor-name">{{ formatCellDoctorSurname(rec) || '\u00a0' }}</span><span
                              v-if="commentForRecordDay(rec, day.key).trim()"
                              class="record-comment-after-doctor"
                              :title="commentForRecordDay(rec, day.key)"
                            > · {{ cellCommentAfterDoctor(rec, day.key) }}</span>
                          </span>
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <aside class="board-patients-aside">
        <h5 class="board-patients-heading">
          Пациенты
        </h5>
        <input
          v-model.trim="unallocatedSearch"
          class="form-control input-sm board-patients-search"
          type="text"
          placeholder="Поиск"
        >
        <div class="board-patients-scroll">
          <p
            v-if="!departmentPk"
            class="text-muted small board-patients-empty"
          >
            Выберите подразделение
          </p>
          <template v-else>
            <div
              v-for="p in unallocatedPatientsFiltered"
              :key="p.direction_pk"
              class="board-patient-row"
              draggable="true"
              @dragstart="onUnallocatedPatientDragStart($event, p)"
              @dragend="onUnallocatedPatientDragEnd"
            >
              <a
                class="board-patient-link"
                target="_blank"
                rel="noopener noreferrer"
                :href="stationarHref(p.direction_pk)"
                :class="unallocatedGenderClass(p)"
                @click.stop
                @mousedown.stop
              >{{ p.short_fio }}</a>
              <i
                class="fa-solid fa-child-reaching board-patient-icon"
                :class="unallocatedGenderClass(p)"
              />
              <span class="board-patient-age">{{ p.age }}л.</span>
            </div>
          </template>
        </div>
      </aside>
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
            v-if="editingRecordPk || editingStripRowId"
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
          <div class="form-group">
            <label>Комментарий на выбранную дату</label>
            <textarea
              v-model.trim="editingForm.commentText"
              class="form-control"
              rows="2"
              maxlength="255"
              placeholder="Только для дня, с которого открыто окно"
            />
            <div class="checkbox edit-modal-comment-replicate">
              <label>
                <input
                  v-model="editingForm.commentReplicateFollowing"
                  type="checkbox"
                >
                Проставить на все следующие дни до даты окончания
              </label>
              <p class="help-block small text-muted">
                Нужна заполненная дата окончания в записи; иначе действует только выбранный день.
              </p>
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
            v-if="editingStripRowId"
            type="button"
            class="btn btn-warning"
            title="Удалить запись из черновика дневного стационара"
            @click="clearStripFromModal"
          >
            Освободить
          </button>
          <button
            v-else-if="editingRecordPk"
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

const DND_UNALLOCATED_DIRECTION = 'application/x-l2-board-unallocated-direction';
const STRIP_LOCALSTORAGE_PREFIX = 'l2-hospitalization-board-strip-v1';

interface UnallocatedPatient {
  direction_pk: number;
  fio: string;
  short_fio: string;
  age: number;
  sex: string;
  service_title?: string;
}

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
  /** YYYY-MM-DD → текст комментария на этот день */
  date_comments?: Record<string, string>;
  /** Дневной стационар (в т.ч. запись в «черновике» доски) */
  is_day_hosp?: boolean;
  forbidden_edit?: boolean;
}

interface StripRow {
  rowId: string;
  records: CalendarRecord[];
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
const defaultHospitalizationPeriodDays = ref(3);
const viewMode = ref<ViewMode>('week');
const anchorDate = ref(moment());
const isEditModalOpen = ref(false);
const editingBedPk = ref<number | null>(null);
const editingDayKey = ref('');
const editingRecordPk = ref<number | null>(null);
const editingStripRowId = ref<string | null>(null);
const editingStripRecordPk = ref<number | null>(null);
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
  commentText: '',
  commentReplicateFollowing: false,
});

const dragOverCellKey = ref('');
const dragOverStripCellKey = ref('');
const hoveredDayKey = ref<string | null>(null);
const suppressCellClick = ref(false);

const newStripRowId = () => (
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `r-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
);

const stripRows = ref<StripRow[]>([{ rowId: newStripRowId(), records: [] }]);

const stripRowIsEmpty = (row: StripRow) => row.records.length === 0;

const normalizeStripRowRecords = (row: { record?: CalendarRecord | null, records?: CalendarRecord[] }): CalendarRecord[] => {
  if (Array.isArray(row.records)) {
    return row.records.filter(Boolean) as CalendarRecord[];
  }
  if (row.record) {
    return [row.record];
  }
  return [];
};

const addRecordToStripRow = (rowIdx: number, record: CalendarRecord): boolean => {
  const row = stripRows.value[rowIdx];
  if (!row) {
    return false;
  }
  if (row.records.some((r) => r.pk === record.pk)) {
    return false;
  }
  if (record.direction_pk != null && record.direction_pk > 0
      && row.records.some((r) => r.direction_pk === record.direction_pk)) {
    return false;
  }
  row.records.push(record);
  return true;
};

const removeStripRecordFromRow = (row: StripRow, recordPk: number) => {
  const idx = row.records.findIndex((r) => r.pk === recordPk);
  if (idx >= 0) {
    row.records.splice(idx, 1);
  }
};

const normalizeStripTrailingEmpty = () => {
  while (
    stripRows.value.length > 1
      && stripRowIsEmpty(stripRows.value[stripRows.value.length - 1])
      && stripRowIsEmpty(stripRows.value[stripRows.value.length - 2])
  ) {
    stripRows.value.pop();
  }
  if (stripRows.value.length === 0) {
    stripRows.value.push({ rowId: newStripRowId(), records: [] });
    return;
  }
  const last = stripRows.value[stripRows.value.length - 1];
  if (!stripRowIsEmpty(last)) {
    stripRows.value.push({ rowId: newStripRowId(), records: [] });
  }
};

const persistStripToStorage = () => {
  const dept = departmentPk.value;
  if (dept == null) {
    return;
  }
  try {
    localStorage.setItem(
      `${STRIP_LOCALSTORAGE_PREFIX}:${dept}`,
      JSON.stringify({ rows: stripRows.value }),
    );
  } catch {
    /* quota / private mode */
  }
};

const initStripRowsForDepartment = (dept: number | null) => {
  if (dept == null) {
    stripRows.value = [{ rowId: newStripRowId(), records: [] }];
    return;
  }
  try {
    const raw = localStorage.getItem(`${STRIP_LOCALSTORAGE_PREFIX}:${dept}`);
    if (raw) {
      const parsed = JSON.parse(raw) as {
        rows?: Array<{ rowId?: string, record?: CalendarRecord | null, records?: CalendarRecord[] }>
      };
      if (Array.isArray(parsed.rows) && parsed.rows.length) {
        stripRows.value = parsed.rows.map((r) => ({
          rowId: (r.rowId && String(r.rowId)) || newStripRowId(),
          records: normalizeStripRowRecords(r),
        }));
        normalizeStripTrailingEmpty();
        return;
      }
    }
  } catch {
    /* ignore */
  }
  stripRows.value = [{ rowId: newStripRowId(), records: [] }];
};

const isRecordPkOnStrip = (pk: number) => stripRows.value.some((r) => r.records.some((rec) => rec.pk === pk));

const removeStripRecordPk = (pk: number) => {
  for (const row of stripRows.value) {
    removeStripRecordFromRow(row, pk);
  }
  normalizeStripTrailingEmpty();
  persistStripToStorage();
};

const unallocatedPatients = ref<UnallocatedPatient[]>([]);
const unallocatedSearch = ref('');

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
    start = anchorDate.value.clone().startOf('day');
    end = anchorDate.value.clone().add(31, 'days').endOf('day');
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

const commentForRecordDay = (rec: CalendarRecord, dayKey: string) => {
  const raw = rec.date_comments?.[dayKey] ?? '';
  return (raw && String(raw)) || '';
};

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

const stripRecordPkSet = computed(() => {
  const s = new Set<number>();
  for (const row of stripRows.value) {
    for (const rec of row.records) {
      s.add(rec.pk);
    }
  }
  return s;
});

const stripDirectionPkSet = computed(() => {
  const s = new Set<number>();
  for (const row of stripRows.value) {
    for (const rec of row.records) {
      const dirPk = rec.direction_pk;
      if (dirPk != null && dirPk > 0) {
        s.add(dirPk);
      }
    }
  }
  return s;
});

const recordsUnfilteredForMainGrid = computed(() => (
  records.value.filter((r) => !stripRecordPkSet.value.has(r.pk))
));

const recordsForMainGrid = computed(() => {
  const list = recordsUnfilteredForMainGrid.value;
  if (doctorPk.value > 0) {
    return list.filter((r) => r.doctor_pk === doctorPk.value);
  }
  return list;
});

const recordByBedAndDay = computed(() => {
  const map = new Map<string, CalendarRecord>();
  const days = visibleDays.value;
  if (!days.length) {
    return map;
  }
  for (const record of recordsForMainGrid.value) {
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

const cellForbiddenEdit = (bedPk: number, dayKey: string) => Boolean(getRecordForDay(bedPk, dayKey)?.forbidden_edit);

const surnameFromFio = (fio: string | null | undefined) => {
  const s = (fio || '').trim();
  if (!s) {
    return '';
  }
  return s.split(/\s+/)[0] || '';
};

const MONTH_CELL_SURNAME_CHARS = 10;
const MONTH_CELL_DIRECTION_CHARS = 7;

/** Режим «месяц»: одна строка, фамилия не длиннее 10 символов */
const monthSurnameShort = (rec: CalendarRecord) => {
  const sur = surnameFromFio(rec.patient_fio);
  if (!sur) {
    return '';
  }
  if (sur.length <= MONTH_CELL_SURNAME_CHARS) {
    return sur;
  }
  return `${sur.slice(0, MONTH_CELL_SURNAME_CHARS)}…`;
};

/** Режим «месяц»: номер направления не длиннее 7 символов */
const monthDirectionIdShort = (directionPk: number) => {
  const s = String(directionPk);
  if (s.length <= MONTH_CELL_DIRECTION_CHARS) {
    return s;
  }
  return `${s.slice(0, MONTH_CELL_DIRECTION_CHARS)}…`;
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

const recordHoverTitle = (rec: CalendarRecord, dayKey: string) => {
  const parts: string[] = [];
  if ((rec.patient_fio || '').trim()) {
    parts.push(rec.patient_fio.trim());
  }
  const age = cellPatientAgePart(rec);
  if (age) {
    parts.push(`Возраст: ${age}`);
  }
  if (rec.direction_pk != null && rec.direction_pk > 0) {
    parts.push(`Направление: ${rec.direction_pk}`);
  }
  const c = commentForRecordDay(rec, dayKey).trim();
  if (c) {
    parts.push(`Комментарий: ${c}`);
  }
  return parts.join(' · ');
};

const formatCellDoctorSurname = (record: CalendarRecord) => surnameFromFio(record.doctor_fio);

const CELL_COMMENT_DISPLAY_MAX = 45;
const CELL_COMMENT_DISPLAY_MAX_MONTH = 22;

const cellCommentAfterDoctor = (record: CalendarRecord, dayKey: string) => {
  const raw = commentForRecordDay(record, dayKey).trim();
  if (!raw) {
    return '';
  }
  const max = viewMode.value === 'month' ? CELL_COMMENT_DISPLAY_MAX_MONTH : CELL_COMMENT_DISPLAY_MAX;
  if (raw.length <= max) {
    return raw;
  }
  return `${raw.slice(0, max)}…`;
};

/** Как в ManageChambers / DirectionsHistory: hash с JSON для экрана стационара */
const stationarHref = (directionPk: number) => (
  `/ui/stationar#{%22pk%22:${directionPk},%22opened_list_key%22:null,%22opened_form_pk%22:null,%22every%22:false}`
);

const cellRecordList = (bedPk: number, dayKey: string): CalendarRecord[] => {
  const r = getRecordForDay(bedPk, dayKey);
  return r ? [r] : [];
};

const stripCellKey = (rowIdx: number, dayKey: string) => `strip-${rowIdx}-${dayKey}`;

const cellStripRecordList = (row: StripRow, dayKey: string): CalendarRecord[] => row.records.filter(
  (rec) => isDayInRecordSpan(rec, dayKey),
);

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

const todayDayKey = computed(() => moment().format('YYYY-MM-DD'));

const isPatientSexMale = (sexRaw: string | null | undefined) => genderColorClass(sexRaw) === 'record-sex--male';

const isPatientSexFemale = (sexRaw: string | null | undefined) => genderColorClass(sexRaw) === 'record-sex--female';

const isTodayDayColumn = (dayKey: string) => dayKey === todayDayKey.value;

type DayColumnTotals = { male: number, female: number, accompanying: number };

const emptyDayColumnTotals = (): DayColumnTotals => ({ male: 0, female: 0, accompanying: 0 });

const dayColumnTotalsMap = computed(() => {
  const map = new Map<string, DayColumnTotals>();
  for (const day of visibleDays.value) {
    map.set(day.key, emptyDayColumnTotals());
  }
  for (const rec of recordsUnfilteredForMainGrid.value) {
    for (const day of visibleDays.value) {
      if (!isDayInRecordSpan(rec, day.key)) {
        continue;
      }
      const t = map.get(day.key) || emptyDayColumnTotals();
      if (isPatientSexMale(rec.patient_sex)) {
        t.male += 1;
      } else if (isPatientSexFemale(rec.patient_sex)) {
        t.female += 1;
      }
      if ((rec.accompanyng_child_type || '').trim()) {
        t.accompanying += 1;
      }
      map.set(day.key, t);
    }
  }
  return map;
});

const dayColumnTotals = (dayKey: string): DayColumnTotals => (
  dayColumnTotalsMap.value.get(dayKey) || emptyDayColumnTotals()
);

/** День для счётчика на бейджах врачей: наведённая колонка, иначе «День» / сегодня */
const doctorBadgeCountDayKey = computed(() => {
  if (hoveredDayKey.value) {
    return hoveredDayKey.value;
  }
  if (viewMode.value === 'day') {
    return anchorDate.value.format('YYYY-MM-DD');
  }
  return todayDayKey.value;
});

const isDayColumnHovered = (dayKey: string) => hoveredDayKey.value === dayKey;

const onDayHeaderMouseEnter = (dayKey: string) => {
  hoveredDayKey.value = dayKey;
};

const onDayHeaderMouseLeave = () => {
  hoveredDayKey.value = null;
};

const addDoctorPatientCountForRecord = (
  map: Map<number, number>,
  rec: CalendarRecord,
  dayKey: string,
) => {
  if (rec.doctor_pk == null || !isDayInRecordSpan(rec, dayKey)) {
    return;
  }
  map.set(rec.doctor_pk, (map.get(rec.doctor_pk) || 0) + 1);
};

const doctorPatientCountMap = computed(() => {
  const dayKey = doctorBadgeCountDayKey.value;
  const map = new Map<number, number>();
  for (const rec of recordsUnfilteredForMainGrid.value) {
    addDoctorPatientCountForRecord(map, rec, dayKey);
  }
  for (const row of stripRows.value) {
    for (const rec of row.records) {
      addDoctorPatientCountForRecord(map, rec, dayKey);
    }
  }
  return map;
});

const doctorPatientCount = (docPk: number) => doctorPatientCountMap.value.get(docPk) || 0;

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

/** Режим «Месяц»: 32 дня от сегодня (сегодня … сегодня+31) */
const setViewMonth = () => {
  anchorDate.value = moment().startOf('day');
  viewMode.value = 'month';
};

const navigate = (direction: number) => {
  if (viewMode.value === 'day') {
    anchorDate.value = anchorDate.value.clone().add(direction, 'day');
  } else if (viewMode.value === 'week') {
    anchorDate.value = anchorDate.value.clone().add(direction, 'week');
  } else {
    anchorDate.value = anchorDate.value.clone().add(direction * 32, 'days');
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

const loadUnallocatedPatients = async () => {
  if (!departmentPk.value) {
    unallocatedPatients.value = [];
    return;
  }
  const row = await api('chambers/get-unallocated-patients', {
    department_pk: departmentPk.value,
  });
  unallocatedPatients.value = Array.isArray(row.data) ? row.data : [];
};

const unallocatedPatientsFiltered = computed(() => {
  const list = unallocatedPatients.value.filter((p) => !stripDirectionPkSet.value.has(p.direction_pk));
  const q = unallocatedSearch.value.trim().toLowerCase();
  if (!q) {
    return list;
  }
  return list.filter((p) => (p.fio || '').toLowerCase().includes(q));
});

const unallocatedGenderClass = (p: UnallocatedPatient) => {
  if (p.sex === 'ж') {
    return 'board-patient--women';
  }
  if (p.sex === 'м') {
    return 'board-patient--man';
  }
  return '';
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
    start_date: start,
    end_date: end,
  });
  chambers.value = response?.data?.chambers || [];
  records.value = response?.data?.records || [];
  const periodDays = Number(response?.data?.default_period_days);
  defaultHospitalizationPeriodDays.value = Number.isFinite(periodDays) && periodDays >= 1
    ? periodDays
    : 3;
  await store.dispatch(actions.DEC_LOADING);
};

const defaultPlanDateOut = (dayKey: string) => {
  const days = defaultHospitalizationPeriodDays.value;
  return moment(dayKey, 'YYYY-MM-DD').add(days - 1, 'days').format('YYYY-MM-DD');
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
  dragOverStripCellKey.value = '';
};

const doctorFioByPk = (docPk: number) => {
  const d = doctors.value.find((x) => x.pk === docPk);
  return (d?.fio || '').trim();
};

const onDoctorStripCellDrop = (rowIdx: number, dayKey: string, docPk: number) => {
  const row = stripRows.value[rowIdx];
  if (!row) {
    root.$emit('msg', 'error', 'Строка черновика не найдена');
    return;
  }
  const dayRecords = cellStripRecordList(row, dayKey);
  if (dayRecords.length === 0) {
    root.$emit('msg', 'error', 'В этой ячейке нет записи — назначить врача некуда');
    return;
  }
  if (dayRecords.length > 1) {
    root.$emit('msg', 'error', 'В ячейке несколько записей — откройте нужную для назначения врача');
    return;
  }
  const recPk = dayRecords[0].pk;
  const recIdx = row.records.findIndex((r) => r.pk === recPk);
  if (recIdx < 0) {
    return;
  }
  row.records[recIdx] = {
    ...row.records[recIdx],
    doctor_pk: docPk,
    doctor_fio: doctorFioByPk(docPk),
  };
  persistStripToStorage();
  root.$emit('msg', 'ok', 'Врач назначен');
};

const onPatientDragStart = (e: DragEvent, rec: CalendarRecord) => {
  e.stopPropagation();
  e.dataTransfer?.setData('application/x-l2-hospitalization-move', String(rec.pk));
  e.dataTransfer?.setData('text/plain', `hosp-move:${rec.pk}`);
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
  }
};

const onStripPatientDragStart = (e: DragEvent, row: StripRow, rec: CalendarRecord) => {
  e.stopPropagation();
  e.dataTransfer?.setData('application/x-l2-strip-row-id', row.rowId);
  e.dataTransfer?.setData('application/x-l2-strip-record-pk', String(rec.pk));
  e.dataTransfer?.setData('text/plain', `strip-row:${row.rowId}:${rec.pk}`);
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
  }
};

const onPatientDragEnd = () => {
  dragOverCellKey.value = '';
  dragOverStripCellKey.value = '';
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

const onStripCellDragOver = (rowIdx: number, dayKey: string) => {
  dragOverStripCellKey.value = stripCellKey(rowIdx, dayKey);
};

const onStripCellDragLeave = (e: DragEvent, rowIdx: number, dayKey: string) => {
  const current = e.currentTarget as Node | null;
  const related = e.relatedTarget as Node | null;
  if (current && related && current.contains(related)) {
    return;
  }
  if (dragOverStripCellKey.value === stripCellKey(rowIdx, dayKey)) {
    dragOverStripCellKey.value = '';
  }
};

const newStripRecordFromUnallocated = (p: UnallocatedPatient, dayKey: string): CalendarRecord => {
  const planOut = defaultPlanDateOut(dayKey);
  return {
    pk: -p.direction_pk,
    bed_pk: 0,
    doctor_pk: null,
    doctor_fio: '',
    patient_fio: p.fio,
    patient_sex: p.sex || 'м',
    birthday: null,
    patient_age_text: String(p.age ?? ''),
    direction_pk: p.direction_pk,
    date_in: dayKey,
    date_out: null,
    plan_date_in: dayKey,
    plan_date_out: planOut,
    accompanyng_child_type: '',
    accompanyng_child_sex: '-',
    date_comments: {},
  };
};

const onUnallocatedToStripDrop = (rowIdx: number, dayKey: string, raw: string) => {
  let directionPk: number;
  try {
    const o = JSON.parse(raw) as { direction_pk?: number };
    directionPk = Number(o.direction_pk);
  } catch {
    root.$emit('msg', 'error', 'Некорректные данные перетаскивания');
    return;
  }
  if (!Number.isFinite(directionPk) || directionPk <= 0) {
    root.$emit('msg', 'error', 'Некорректное направление');
    return;
  }
  if (stripDirectionPkSet.value.has(directionPk)) {
    root.$emit('msg', 'error', 'Пациент уже в черновике');
    return;
  }
  const patient = unallocatedPatients.value.find((p) => p.direction_pk === directionPk);
  if (!patient) {
    root.$emit('msg', 'error', 'Пациент не найден в списке нераспределённых');
    return;
  }
  const record = newStripRecordFromUnallocated(patient, dayKey);
  if (!addRecordToStripRow(rowIdx, record)) {
    root.$emit('msg', 'error', 'Не удалось добавить запись в эту строку черновика');
    return;
  }
  normalizeStripTrailingEmpty();
  persistStripToStorage();
  root.$emit('msg', 'ok', 'Пациент добавлен в черновик');
};

const onStripCellDrop = async (e: DragEvent, rowIdx: number, dayKey: string) => {
  dragOverStripCellKey.value = '';
  const panelDir = e.dataTransfer?.getData(DND_UNALLOCATED_DIRECTION);
  if (panelDir) {
    onUnallocatedToStripDrop(rowIdx, dayKey, panelDir);
    return;
  }
  const docFromMime = e.dataTransfer?.getData('application/x-l2-doctor-pk') || '';
  const plain = e.dataTransfer?.getData('text/plain') || '';
  const docRaw = docFromMime || (plain.startsWith('hosp-move:') || plain.startsWith('strip-row:') ? '' : plain);
  if (docRaw && !docRaw.startsWith('hosp-move:') && !docRaw.startsWith('strip-row:')) {
    const docPk = Number.parseInt(docRaw, 10);
    if (!Number.isNaN(docPk)) {
      onDoctorStripCellDrop(rowIdx, dayKey, docPk);
      return;
    }
  }
  const hospMove = e.dataTransfer?.getData('application/x-l2-hospitalization-move');
  if (!hospMove) {
    return;
  }
  const recordPk = Number.parseInt(hospMove, 10);
  if (Number.isNaN(recordPk)) {
    return;
  }
  const rec = records.value.find((r) => r.pk === recordPk);
  if (!rec) {
    root.$emit('msg', 'error', 'Запись не найдена');
    return;
  }
  if (!isDayInRecordSpan(rec, dayKey)) {
    root.$emit('msg', 'error', 'Дата вне периода госпитализации');
    return;
  }
  if (isRecordPkOnStrip(recordPk)) {
    root.$emit('msg', 'error', 'Запись уже в черновике');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const { ok: okClear, message: msgClear } = await api('chambers/clear-patient-from-bed', {
    record_pk: recordPk,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (!okClear) {
    root.$emit('msg', 'error', msgClear || 'Не удалось освободить койку');
    return;
  }
  if (!addRecordToStripRow(rowIdx, { ...rec })) {
    root.$emit('msg', 'error', 'Не удалось добавить запись в эту строку черновика');
    return;
  }
  normalizeStripTrailingEmpty();
  persistStripToStorage();
  await loadCalendar();
};

const onUnallocatedPatientDragStart = (e: DragEvent, p: UnallocatedPatient) => {
  e.stopPropagation();
  e.dataTransfer?.setData(DND_UNALLOCATED_DIRECTION, JSON.stringify({ direction_pk: p.direction_pk }));
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'copy';
  }
};

const onUnallocatedPatientDragEnd = () => {
  dragOverCellKey.value = '';
  dragOverStripCellKey.value = '';
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
  const fromStrip = isRecordPkOnStrip(recordPk);
  if (sourceRec.bed_pk === targetBedPk) {
    if (!fromStrip) {
      root.$emit('msg', 'error', 'Выберите другую койку');
      return;
    }
    removeStripRecordPk(recordPk);
    await loadCalendar();
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('chambers/move-hospitalization-to-bed', {
    department_pk: departmentPk.value,
    record_pk: recordPk,
    target_bed_id: targetBedPk,
    move_from_date: targetDayKey,
  });
  if (ok) {
    removeStripRecordPk(recordPk);
  }
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Пациент перенесён');
    await loadCalendar();
    await loadUnallocatedPatients();
  } else {
    root.$emit('msg', 'error', message || 'Не удалось перенести пациента');
  }
};

const onStripToBedDrop = async (
  targetBedPk: number,
  targetDayKey: string,
  stripRowId: string,
  stripRecordPkRaw?: string,
) => {
  if (!departmentPk.value) {
    return;
  }
  const row = stripRows.value.find((r) => r.rowId === stripRowId);
  if (!row) {
    root.$emit('msg', 'error', 'Строка черновика не найдена');
    return;
  }
  let record: CalendarRecord | null = null;
  if (stripRecordPkRaw) {
    const stripRecordPk = Number.parseInt(stripRecordPkRaw, 10);
    if (!Number.isNaN(stripRecordPk)) {
      record = row.records.find((r) => r.pk === stripRecordPk) || null;
    }
  }
  if (!record && row.records.length === 1) {
    [record] = row.records;
  }
  if (!record) {
    root.$emit('msg', 'error', 'Запись в черновике не найдена');
    return;
  }
  if (!isDayInRecordSpan(record, targetDayKey)) {
    root.$emit('msg', 'error', 'Нельзя вернуть запись на дату вне периода госпитализации');
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const result = await api('chambers/save-hospitalization-by-fio', {
    department_pk: departmentPk.value,
    bed_id: targetBedPk,
    doctor_id: record.doctor_pk ?? null,
    direction_id: record.direction_pk ?? null,
    patient_fio_text: record.patient_fio || '',
    patient_sex: record.patient_sex || 'м',
    birthday: record.birthday || null,
    patient_age_text: record.patient_age_text || '',
    plan_date_in: record.plan_date_in || record.date_in || targetDayKey,
    plan_date_out: record.plan_date_out || record.date_out || null,
    accompanyng_child_type: record.accompanyng_child_type || '',
    comment_date: targetDayKey,
    comment: commentForRecordDay(record, targetDayKey),
  });
  await store.dispatch(actions.DEC_LOADING);
  if (result?.ok) {
    removeStripRecordFromRow(row, record.pk);
    normalizeStripTrailingEmpty();
    persistStripToStorage();
    root.$emit('msg', 'ok', 'Запись возвращена на койку');
    await loadCalendar();
    await loadUnallocatedPatients();
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось вернуть запись на койку');
  }
};

const onDirectionFromPanelDrop = async (bedPk: number, dayKey: string, raw: string) => {
  if (!departmentPk.value) {
    return;
  }
  let directionPk: number;
  try {
    const o = JSON.parse(raw) as { direction_pk?: number };
    directionPk = Number(o.direction_pk);
  } catch {
    root.$emit('msg', 'error', 'Некорректные данные перетаскивания');
    return;
  }
  if (!Number.isFinite(directionPk) || directionPk <= 0) {
    root.$emit('msg', 'error', 'Некорректное направление');
    return;
  }
  const record = getRecordForDay(bedPk, dayKey);
  await store.dispatch(actions.INC_LOADING);
  let result;
  if (record?.pk) {
    result = await api('chambers/update-hospitalization-record', {
      record_pk: record.pk,
      doctor_id: record.doctor_pk ?? null,
      patient_fio_text: record.patient_fio || '',
      patient_sex: record.patient_sex || 'м',
      birthday: record.birthday || null,
      patient_age_text: record.patient_age_text || '',
      plan_date_in: record.plan_date_in || record.date_in || null,
      plan_date_out: record.plan_date_out || record.date_out || null,
      accompanyng_child_type: record.accompanyng_child_type || '',
      direction_id: directionPk,
      comment_date: dayKey,
      comment: commentForRecordDay(record, dayKey),
    });
  } else {
    result = await api('chambers/save-hospitalization-by-fio', {
      department_pk: departmentPk.value,
      bed_id: bedPk,
      doctor_id: null,
      direction_id: directionPk,
      patient_fio_text: '',
      patient_sex: 'м',
      birthday: null,
      patient_age_text: '',
      plan_date_in: dayKey,
      plan_date_out: null,
      auto_default_period: true,
      fill_patient_from_direction: true,
      accompanyng_child_type: '',
      comment_date: dayKey,
      comment: '',
    });
  }
  await store.dispatch(actions.DEC_LOADING);
  if (result?.ok) {
    root.$emit('msg', 'ok', record?.pk ? 'Направление привязано' : 'Госпитализация создана');
    await loadCalendar();
    await loadUnallocatedPatients();
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось выполнить операцию');
  }
};

const onCellDrop = async (e: DragEvent, bedPk: number, dayKey: string) => {
  dragOverCellKey.value = '';
  const panelDir = e.dataTransfer?.getData(DND_UNALLOCATED_DIRECTION);
  if (panelDir) {
    await onDirectionFromPanelDrop(bedPk, dayKey, panelDir);
    return;
  }
  const stripRowId = e.dataTransfer?.getData('application/x-l2-strip-row-id');
  if (stripRowId) {
    const stripRecordPk = e.dataTransfer?.getData('application/x-l2-strip-record-pk') || '';
    await onStripToBedDrop(bedPk, dayKey, stripRowId, stripRecordPk);
    return;
  }
  const hospMove = e.dataTransfer?.getData('application/x-l2-hospitalization-move');
  if (hospMove) {
    await onPatientBedDrop(bedPk, dayKey, hospMove);
    return;
  }
  const docFromMime = e.dataTransfer?.getData('application/x-l2-doctor-pk') || '';
  const plain = e.dataTransfer?.getData('text/plain') || '';
  const docRaw = docFromMime || (plain.startsWith('hosp-move:') ? '' : plain);
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
    comment_date: dayKey,
    comment: commentForRecordDay(record, dayKey),
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Врач назначен');
    await loadCalendar();
    await loadUnallocatedPatients();
  } else {
    root.$emit('msg', 'error', message || 'Не удалось назначить врача');
  }
};

const closeEditModal = () => {
  isEditModalOpen.value = false;
  editingBedPk.value = null;
  editingDayKey.value = '';
  editingRecordPk.value = null;
  editingStripRowId.value = null;
  editingStripRecordPk.value = null;
};

const fillEditModalFromRecord = (record: CalendarRecord | null, bedPk: number, dayKey: string) => {
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
    planDateOut: record?.plan_date_out || record?.date_out || defaultPlanDateOut(dayKey),
    doctorPk: record?.doctor_pk ?? null,
    doctorFio: (record?.doctor_fio || '').trim(),
    accompanyngChildType: (record?.accompanyng_child_type && String(record.accompanyng_child_type).trim()) || null,
    commentText: record ? commentForRecordDay(record, dayKey) : '',
    commentReplicateFollowing: false,
  };
};

const openEditModal = (bedPk: number, dayKey: string) => {
  if (suppressCellClick.value) {
    return;
  }
  editingStripRowId.value = null;
  const record = getRecordForDay(bedPk, dayKey);
  fillEditModalFromRecord(record ?? null, bedPk, dayKey);
  isEditModalOpen.value = true;
};

const openStripRecordModal = (rowIdx: number, dayKey: string, record: CalendarRecord) => {
  if (suppressCellClick.value) {
    return;
  }
  const row = stripRows.value[rowIdx];
  if (!row || !isDayInRecordSpan(record, dayKey)) {
    return;
  }
  editingStripRowId.value = row.rowId;
  editingStripRecordPk.value = record.pk;
  fillEditModalFromRecord(record, record.bed_pk, dayKey);
  editingRecordPk.value = null;
  isEditModalOpen.value = true;
};

const openStripCellModal = (rowIdx: number, dayKey: string) => {
  if (suppressCellClick.value) {
    return;
  }
  const row = stripRows.value[rowIdx];
  if (!row) {
    return;
  }
  const dayRecords = cellStripRecordList(row, dayKey);
  if (dayRecords.length === 1) {
    openStripRecordModal(rowIdx, dayKey, dayRecords[0]);
  }
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

  if (editingForm.value.planDateIn && editingForm.value.planDateOut
      && editingForm.value.planDateIn > editingForm.value.planDateOut) {
    root.$emit('msg', 'error', 'Дата начала не может быть позже даты окончания');
    return;
  }
  const commentPayload = editingForm.value.commentText.trim().slice(0, 255);
  if (editingStripRowId.value) {
    const row = stripRows.value.find((r) => r.rowId === editingStripRowId.value);
    const rec = row?.records.find((r) => r.pk === editingStripRecordPk.value) || null;
    if (!row || !rec) {
      root.$emit('msg', 'error', 'Запись черновика не найдена');
      return;
    }
    rec.patient_fio = editingForm.value.patientFioText;
    rec.patient_sex = editingForm.value.patientSex || 'м';
    rec.birthday = editingForm.value.birthday || null;
    rec.patient_age_text = editingForm.value.patientAgeText;
    rec.plan_date_in = editingForm.value.planDateIn || null;
    rec.plan_date_out = editingForm.value.planDateOut || null;
    rec.date_in = editingForm.value.planDateIn || rec.date_in;
    rec.date_out = editingForm.value.planDateOut || rec.date_out;
    rec.doctor_pk = editingForm.value.doctorPk;
    rec.doctor_fio = editingForm.value.doctorFio;
    rec.accompanyng_child_type = editingForm.value.accompanyngChildType || '';
    rec.direction_pk = directionIdPayload;
    rec.date_comments = { ...(rec.date_comments || {}), [editingDayKey.value]: commentPayload };
    persistStripToStorage();
    root.$emit('msg', 'ok', 'Данные черновика сохранены');
    closeEditModal();
    return;
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
      comment_date: editingDayKey.value,
      comment: commentPayload,
      comment_replicate_following: editingForm.value.commentReplicateFollowing,
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
      comment_date: editingDayKey.value,
      comment: commentPayload,
      comment_replicate_following: editingForm.value.commentReplicateFollowing,
    });
  }
  await store.dispatch(actions.DEC_LOADING);
  if (result?.ok) {
    root.$emit('msg', 'ok', 'Данные сохранены');
    closeEditModal();
    await loadCalendar();
    await loadUnallocatedPatients();
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось сохранить запись');
  }
};

const clearStripFromModal = () => {
  if (!editingStripRowId.value || editingStripRecordPk.value == null) {
    return;
  }
  const row = stripRows.value.find((r) => r.rowId === editingStripRowId.value);
  if (!row) {
    root.$emit('msg', 'error', 'Запись черновика не найдена');
    return;
  }
  removeStripRecordFromRow(row, editingStripRecordPk.value);
  normalizeStripTrailingEmpty();
  persistStripToStorage();
  root.$emit('msg', 'ok', 'Запись удалена из дневного стационара');
  closeEditModal();
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
    await loadUnallocatedPatients();
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось освободить койку');
  }
};

watch([departmentPk, viewMode, anchorDate], async () => {
  await loadCalendar();
  await loadUnallocatedPatients();
});

watch(departmentPk, async (d) => {
  await loadDoctors();
  doctorPk.value = -1;
  initStripRowsForDepartment(d);
});

onMounted(async () => {
  await Promise.all([loadDepartments(), loadAccompanyingChildOptions()]);
});
</script>

<style scoped lang="scss">
.board-page {
  padding: 10px 16px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
  min-height: 0;
  box-sizing: border-box;
}

.board-body {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  flex: 1;
  min-height: 0;
  min-width: 0;
}

.board-patients-aside {
  flex: 0 0 280px;
  width: 280px;
  max-width: 280px;
  border-left: 1px solid #ddd;
  padding: 0 0 8px 12px;
  margin-left: 8px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: hsla(30, 3%, 97%, 1);
}

.board-patients-heading {
  text-align: center;
  margin: 8px 0 6px;
  font-size: 14px;
  font-weight: 600;
}

.board-patients-search {
  margin-bottom: 8px;
}

.board-patients-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.board-patient-row {
  margin: 5px 0;
  padding: 6px 8px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  cursor: grab;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 13px;
}

.board-patient-row:active {
  cursor: grabbing;
}

.board-patient-link {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.board-patient-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.board-patient-age {
  flex-shrink: 0;
  color: #333;
}

.board-patient--women {
  color: #ff73ea;
}

.board-patient--man {
  color: #00bfff;
}

.toolbar {
  margin-bottom: 8px;
  flex-shrink: 0;
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
  display: flex;
  flex-direction: column;
  width: 100%;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  container-type: inline-size;
  container-name: calendar-wrap;
}

.calendar-tables-stack {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.calendar-main-scroll {
  flex: 3 1 0;
  min-height: 0;
  overflow: auto;
}

.calendar-strip-block {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  margin-top: 0;
  padding-top: 8px;
  border-top: 1px solid #ddd;
}

.calendar-strip-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.doctor-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0 0 8px;
  flex-shrink: 0;
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
  width: 100%;
  min-width: 0;
}

/* Месяц: столбец даты в 2 раза уже, чем столбец даты недели (доля (100%−фикс)/7 пополам) */
.calendar-table--month {
  width: auto;
  min-width: 100%;
}

.calendar-table--month .calendar-col-day {
  width: calc((100cqi - 112px - 64px) / 7 / 2);
  min-width: 0;
}

.calendar-table--month .day-col,
.calendar-table--month .day-cell {
  width: calc((100cqi - 112px - 64px) / 7 / 2);
  min-width: 0;
  max-width: calc((100cqi - 112px - 64px) / 7 / 2);
}

.calendar-table--month .day-cell {
  overflow: hidden;
}

.calendar-table--month .record-line--patient {
  flex-wrap: nowrap;
  gap: 6px;
}

.calendar-table--month .record-patient {
  flex: 1 1 auto;
  min-width: 0;
  flex-wrap: nowrap;
  white-space: nowrap;
  overflow: hidden;
}

.calendar-table--month .record-patient-surname {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 11em;
}

.calendar-table--month .record-line-actions {
  flex-shrink: 0;
}

.calendar-col-chamber {
  width: 112px;
}

.calendar-col-bed {
  width: 64px;
}

.calendar-col-day {
  width: auto;
}

.chamber-col {
  width: 112px;
  min-width: 112px;
  max-width: 112px;
}

.bed-col {
  width: 64px;
  min-width: 64px;
  max-width: 64px;
}

.day-col {
  width: auto;
  min-width: 0;
  text-align: center;
}

.day-col--today {
  background: #fafafa;
}

.day-col--header {
  cursor: default;
}

.day-col--hover,
.day-cell--col-hover {
  background: rgba(4, 147, 114, 0.1);
}

.day-col--today.day-col--hover {
  background: rgba(4, 147, 114, 0.14);
}

.day-cell--col-hover.day-cell--forbidden-edit {
  background: #e4e4e4;
}

.day-col-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  line-height: 1.2;
}

.day-col-totals {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  color: #555;
  white-space: nowrap;
}

.day-col-totals-item {
  display: inline;
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
  left: 112px;
}

.chamber-cell {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  width: auto;
  min-width: 0;
  overflow: hidden;
}

.day-cell--forbidden-edit {
  background: #f0f0f0;
}

.day-cell--drop-hover {
  box-shadow: inset 0 0 0 2px #049372;
  background: rgba(4, 147, 114, 0.12);
}

.record {
  background: transparent;
  color: inherit;
  font-size: 12px;
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

.record-patient-name-wrap {
  display: inline-flex;
  align-items: baseline;
  flex-wrap: nowrap;
  width: fit-content;
  max-width: 100%;
  border-bottom: 1px solid #bbb;
  padding-bottom: 1px;
  margin-bottom: 2px;
  vertical-align: baseline;
  min-width: 0;
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

.record-line--doctor {
  font-weight: 500;
  color: #555;
  font-size: 10px;
  min-height: 1.1em;
  margin-top: 2px;
  min-width: 0;
}

.record-doctor-line-inner {
  display: block;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-doctor-name {
  font-weight: 500;
  color: #555;
}

.record-comment-after-doctor {
  font-weight: 400;
  color: #777;
}

.record-line-actions {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.record-direction-link {
  font-size: 12px;
  font-weight: 600;
  color: #0d47a1;
  text-decoration: underline;
  cursor: pointer;
  flex-shrink: 0;
}

.record-direction-link:hover,
.record-direction-link:focus {
  color: #1565c0;
}

.record-accompany-letter {
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  user-select: none;
}

.record-day-hosp-badge {
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  user-select: none;
  margin-left: 4px;
  padding: 1px 4px;
  border-radius: 3px;
  background: #e8f5e9;
  color: #2e7d32;
}

.record-sex--male {
  color: #00bfff;
}

.record-sex--female {
  color: #ff73ea;
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

.edit-modal-comment-replicate {
  margin-top: 8px;
}

.edit-modal-comment-replicate .help-block {
  margin-bottom: 0;
}

.strip-board-hint {
  margin: 0 0 6px;
  flex-shrink: 0;
}

.calendar-table--strip {
  background: #fafafa;
}

.calendar-col-strip-sidebar {
  width: 176px;
}

.strip-sidebar-col {
  width: 176px;
  min-width: 176px;
  max-width: 176px;
}

.strip-sidebar-th {
  font-size: 12px;
  font-weight: 600;
  vertical-align: middle;
}

.strip-sidebar-cell {
  text-align: center;
  color: #888;
  vertical-align: middle;
}

.calendar-table--strip .strip-sidebar-col.sticky-col {
  left: 0;
  background: #f5f5f5;
  z-index: 3;
}

.calendar-table--strip.calendar-table--month {
  width: auto;
  min-width: 100%;
}

.calendar-table--strip.calendar-table--month .calendar-col-day {
  width: calc((100cqi - 176px) / 7 / 2);
  min-width: 0;
}

.calendar-table--strip.calendar-table--month .day-col,
.calendar-table--strip.calendar-table--month .day-cell {
  width: calc((100cqi - 176px) / 7 / 2);
  min-width: 0;
  max-width: calc((100cqi - 176px) / 7 / 2);
}

.calendar-table--strip.calendar-table--month .day-cell {
  overflow: hidden;
}
</style>
