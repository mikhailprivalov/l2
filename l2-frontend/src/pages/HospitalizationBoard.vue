<template>
  <div class="board-page">
    <div class="toolbar panel panel-default panel-flt">
      <div class="panel-body">
        <div class="toolbar-layout">
          <div class="toolbar-calendar-col">
            <div class="toolbar-row">
              <div class="toolbar-department">
                <Treeselect
                  v-model="departmentPk"
                  :options="departments"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :clearable="false"
                  :append-to-body="true"
                  placeholder="Подразделение"
                  class="treeselect-wide treeselect-34px toolbar-department-treeselect"
                />
              </div>
              <div class="toolbar-controls toolbar-controls--nav">
            <div
              class="mode-switch"
              :class="{ 'mode-switch--period-frozen': isCustomPeriodActive }"
            >
              <label
                v-if="canUseCustomPeriod"
                class="toolbar-period-toggle"
              >
                <input
                  v-model="isCustomPeriodMode"
                  type="checkbox"
                >
                Период
              </label>
              <div
                v-if="isCustomPeriodActive"
                class="toolbar-custom-period"
              >
                <input
                  v-model="customPeriodStart"
                  class="form-control toolbar-custom-period-input"
                  type="date"
                  :max="customPeriodEnd || customPeriodEndMax"
                >
                <span class="toolbar-custom-period-sep">-</span>
                <input
                  v-model="customPeriodEnd"
                  class="form-control toolbar-custom-period-input"
                  type="date"
                  :min="customPeriodStart"
                  :max="customPeriodEndMax"
                >
              </div>
              <button
                class="btn btn-default"
                :class="{ active: viewMode === 'day' && !isCustomPeriodActive }"
                :disabled="isCustomPeriodActive"
                @click="viewMode = 'day'"
              >
                День
              </button>
              <button
                class="btn btn-default"
                :class="{ active: viewMode === 'week' && !isCustomPeriodActive }"
                :disabled="isCustomPeriodActive"
                @click="viewMode = 'week'"
              >
                Неделя
              </button>
              <button
                class="btn btn-default"
                :class="{ active: viewMode === 'month' && !isCustomPeriodActive }"
                :disabled="isCustomPeriodActive"
                @click="setViewMonth"
              >
                Месяц
              </button>
              <button
                type="button"
                class="btn btn-default"
                title="Обновить"
                @click="refreshBoard"
              >
                <i class="fa-solid fa-rotate" />
              </button>
            </div>
            <div
              class="btn-group"
              :class="{ 'btn-group--period-frozen': isCustomPeriodActive }"
            >
              <button
                class="btn btn-default"
                :disabled="isCustomPeriodActive"
                @click="navigate(-1)"
              >
                ←
              </button>
              <button
                class="btn btn-default"
                :disabled="isCustomPeriodActive"
                @click="goToday"
              >
                Текущий
              </button>
              <button
                class="btn btn-default"
                :disabled="isCustomPeriodActive"
                @click="navigate(1)"
              >
                →
              </button>
            </div>
              </div>
            </div>
            <div class="doctor-badges doctor-badges--toolbar">
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
                :key="`doctor-${doctor.pk}`"
                type="button"
                draggable="true"
                class="badge badge-secondary doctor-badge-btn doctor-badge-draggable"
                :class="{ active: doctorPk === doctor.pk }"
                @click="doctorPk = doctor.pk"
                @dragstart="onDoctorDragStart($event, doctor.pk)"
                @dragend="onDoctorDragEnd"
              >
                {{ doctor.short_fio || doctor.fio }} - {{ doctorPatientCount(doctor.pk) }}
              </button>
            </div>
          </div>
          <div class="toolbar-aside-panel">
            <div class="toolbar-aside-search-row">
              <div class="toolbar-aside-search-wrap">
                <input
                  v-model.trim="unallocatedSearch"
                  class="form-control toolbar-aside-search"
                  type="text"
                  placeholder="Поиск по ФИО"
                >
                <button
                  v-if="unallocatedSearch"
                  type="button"
                  class="toolbar-aside-search-clear"
                  title="Очистить поиск"
                  tabindex="-1"
                  @click="unallocatedSearch = ''"
                >
                  <i class="fa-solid fa-xmark" />
                </button>
              </div>
              <div class="board-aside-scroll-controls board-aside-scroll-controls--toolbar">
              <button
                type="button"
                class="btn btn-default btn-sm board-aside-scroll-btn board-aside-scroll-btn--toolbar"
                title="Сдвинуть списки выше"
                :disabled="!canAsideScrollUp"
                @mousedown.prevent="startAsideScrollHold(-1)"
                @mouseup="stopAsideScrollHold"
                @mouseleave="stopAsideScrollHold"
                @touchstart.prevent="startAsideScrollHold(-1)"
                @touchend="stopAsideScrollHold"
                @touchcancel="stopAsideScrollHold"
              >
                ↑
              </button>
              <button
                type="button"
                class="btn btn-default btn-sm board-aside-scroll-btn board-aside-scroll-btn--toolbar"
                title="Сдвинуть списки ниже"
                @mousedown.prevent="startAsideScrollHold(1)"
                @mouseup="stopAsideScrollHold"
                @mouseleave="stopAsideScrollHold"
                @touchstart.prevent="startAsideScrollHold(1)"
                @touchend="stopAsideScrollHold"
                @touchcancel="stopAsideScrollHold"
              >
                ↓
              </button>
              <button
                type="button"
                class="btn btn-default btn-sm board-aside-scroll-btn board-aside-scroll-btn--toolbar"
                title="В начало списков"
                :disabled="asideScrollOffset <= 0"
                @click="resetAsideScroll"
              >
                ⌂
              </button>
              </div>
            </div>
            <div class="toolbar-quick-filters">
              <label
                class="toolbar-quick-filter"
                title="Мужчины"
              >
                <input
                  v-model="quickFilterMale"
                  type="checkbox"
                >
                М
              </label>
              <label
                class="toolbar-quick-filter"
                title="Женщины"
              >
                <input
                  v-model="quickFilterFemale"
                  type="checkbox"
                >
                Ж
              </label>
              <label
                class="toolbar-quick-filter"
                title="Сопровождающий ребёнка"
              >
                <input
                  v-model="quickFilterAccompanying"
                  type="checkbox"
                >
                С
              </label>
              <label
                class="toolbar-quick-filter"
                title="Выписаны"
              >
                <input
                  v-model="quickFilterExtract"
                  type="checkbox"
                >
                В
              </label>
              <label
                class="toolbar-quick-filter"
                title="Свободные койки"
              >
                <input
                  v-model="quickFilterFree"
                  type="checkbox"
                >
                Н
              </label>
              <label
                class="toolbar-quick-filter"
                title="Требуется больничный"
              >
                <input
                  v-model="quickFilterSick"
                  type="checkbox"
                >
                Б
              </label>
              <label
                class="toolbar-quick-filter"
                title="Дубли: фамилия и номер направления"
              >
                <input
                  v-model="quickFilterClone"
                  type="checkbox"
                >
                <i class="fa-regular fa-clone" />
              </label>
              <span
                v-if="quickFilterPeriodCountSummary"
                class="toolbar-quick-filter-counts"
                title="Уникальные записи за выбранный период"
              >
                {{ quickFilterPeriodCountSummary }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      ref="boardBodyRef"
      class="board-body"
    >
      <div
        ref="calendarWrapRef"
        class="calendar-wrap"
      >
        <div class="calendar-tables-stack">
          <div
            class="calendar-main-scroll"
            :class="{ 'calendar-main-scroll--search-compact': hasBoardPatientFilters }"
          >
            <table
              class="table table-bordered table-condensed calendar-table"
              :class="{ 'calendar-table--month': viewMode === 'month' && !isCustomPeriodActive }"
              :style="{ minWidth: `${mainCalendarTableMinWidthPx}px` }"
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
                        <span class="day-col-totals-item">В-{{ extractCountForDay(day.key) }}</span>
                        <span class="day-col-totals-item">Н-{{ dayColumnTotals(day.key).free }}</span>
                      </div>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody>
                <template v-for="row in chamberRowsForDisplay">
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
                        :class="{ 'record--extract': isRecordDischargeDay(rec, day.key) }"
                      :style="duplicateHighlightStyleForRecord(rec)"
                        draggable="true"
                        :title="recordHoverTitle(rec, day.key)"
                        @click.stop="openEditModalForRecord(bed.pk, day.key, rec)"
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
                                  <template v-if="viewMode === 'month' && !isCustomPeriodActive">
                                    {{ monthSurnameShort(rec) }}
                                  </template>
                                  <template v-else>
                                    {{ surnameFromFio(rec.patient_fio) }}
                                  </template>
                                </span><span
                                  v-if="(viewMode !== 'month' || isCustomPeriodActive) && cellPatientAgePart(rec)"
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
                              @click.stop
                              @mousedown.stop
                            >
                              <template v-if="viewMode === 'month' && !isCustomPeriodActive">
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
                          <span
                            v-if="rec.is_need_sick"
                            class="record-sick-badge"
                            title="Требуется больничный"
                          >Б</span>
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
                <tr v-if="chamberRowsForDisplay.length === 0">
                  <td
                    colspan="100"
                    class="text-center"
                  >
                    {{
                      hasBoardPatientFilters
                        ? 'Нет пациентов по фильтрам в таблице коек'
                        : 'Нет палат или данных за выбранный период'
                    }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="strip-board-block calendar-strip-block">
            <p class="strip-board-hint">
              Дневные — {{ stripRecordsInPeriodNotExtractCount }}
            </p>
            <div
              class="strip-cards-board"
              :class="{
                'strip-cards-board--drop-hover': dragOverStripBoard,
                'strip-cards-board--extra-drop-row': stripNeedsExtraDropRow,
              }"
              @dragover.prevent="onStripBoardDragOver"
              @dragleave="onStripBoardDragLeave"
              @drop.prevent="onStripBoardDrop"
            >
              <p
                v-if="!departmentPk"
                class="text-muted small strip-cards-empty"
              >
                Выберите подразделение
              </p>
              <p
                v-else-if="!stripRecordsInPeriod.length"
                class="text-muted small strip-cards-empty"
              >
                {{ hasBoardPatientFilters ? 'Нет пациентов по фильтрам' : 'Нет пациентов за выбранный период' }}
              </p>
              <div
                v-for="rec in stripRecordsInPeriod"
                :key="`strip-card-${rec.pk}-${rec.direction_pk}`"
                class="strip-card record record--draggable"
                :class="{
                  'strip-card--forbidden-edit': rec.is_extract,
                  'strip-card--drop-hover': dragOverStripRecordPk === rec.pk,
                }"
                :style="duplicateHighlightStyleForRecord(rec)"
                draggable="true"
                :title="recordHoverTitle(rec, stripDefaultDayKey)"
                @dragstart.stop="onStripPatientDragStart($event, rec)"
                @dragend="onPatientDragEnd"
                @click.stop="openStripRecordModal(rec)"
                @dragover.prevent.stop="onStripCardDragOver(rec)"
                @dragleave.stop="onStripCardDragLeave($event, rec)"
                @drop.prevent.stop="onStripCardDrop($event, rec)"
              >
                <div class="record-line record-line--patient">
                  <span class="record-patient">
                    <span class="record-patient-name-wrap">
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
                  </span>
                  <span class="record-line-actions">
                    <a
                      v-if="rec.direction_pk != null && rec.direction_pk > 0"
                      :href="stationarHref(rec.direction_pk)"
                      class="record-direction-link"
                      target="_blank"
                      rel="noopener noreferrer"
                      @click.stop
                      @mousedown.stop
                    >{{ rec.direction_pk }}</a>
                    <span
                      v-if="accompanyingDisplayLetter(rec)"
                      class="record-accompany-letter"
                      :class="genderColorClass(rec.accompanyng_child_sex)"
                      :title="accompanyingLetterTitle(rec)"
                    >{{ accompanyingDisplayLetter(rec) }}</span>
                  </span>
                </div>
                <div class="record-line record-line--doctor">
                  <span class="record-doctor-line-inner">
                    <span class="record-doctor-name">{{ formatCellDoctorSurname(rec) || '\u00a0' }}</span>
                  </span>
                  <span class="strip-card-doctor-aside">
                    <span
                      v-if="rec.is_need_sick"
                      class="record-sick-badge"
                      title="Требуется больничный"
                    >Б</span>
                    <span class="strip-card-period">{{ formatStripPeriodLabel(rec) }}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <aside
        ref="boardPatientsAside"
        class="board-patients-aside"
        :style="asideColumnStyle"
      >
        <div
          ref="boardAsideViewport"
          class="board-aside-viewport"
          :style="asideColumnStyle"
        >
          <div
            ref="boardAsideContent"
            class="board-aside-content"
            :style="{ transform: `translateY(${asideScrollOffset}px)` }"
          >
            <section class="board-aside-section board-aside-section--patients">
              <div class="board-patients-heading-row">
                <h5 class="board-patients-heading">
                  Без коек — {{ unallocatedPatientsFiltered.length }}
                </h5>
              </div>
              <div class="board-aside-section-body">
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
                    :style="duplicateHighlightStyleForUnallocated(p)"
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
            </section>

            <section class="board-aside-section board-aside-section--discharged">
              <div class="board-patients-heading-row board-discharged-heading-row">
                <h5 class="board-patients-heading board-discharged-heading">
                  <a
                    href="#"
                    class="board-discharged-heading-link"
                    @click.prevent="openExtractsDetailForm"
                  >Выписаны - {{ extractsCount }}</a>
                </h5>
              </div>
              <div class="board-aside-section-body">
                <p
                  v-if="!departmentPk"
                  class="text-muted small board-patients-empty"
                >
                  Выберите подразделение
                </p>
                <p
                  v-else-if="!hasDischargedInPeriod"
                  class="text-muted small board-patients-empty"
                >
                  Нет выписок за выбранный период
                </p>
                <template v-else>
                  <div
                    v-for="row in dischargedPatientsInPeriod"
                    :key="row.key"
                    class="board-patient-row board-patient-row--discharged"
                  >
                    <a
                      class="board-patient-link"
                      target="_blank"
                      rel="noopener noreferrer"
                      :href="stationarHref(row.directionPk)"
                      @click.stop
                      @mousedown.stop
                    >{{ row.name }}</a>
                    <span class="board-discharged-date">{{ row.dateLabel }}</span>
                  </div>
                </template>
              </div>
            </section>
          </div>
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
            <div class="treeselect-noborder-left edit-modal-treeselect">
              <Treeselect
                :value="editingForm.doctorPk"
                :options="attendingDoctorTreeselectOptions"
                :multiple="false"
                :disable-branch-nodes="true"
                :clearable="true"
                :append-to-body="true"
                :z-index="10050"
                class="treeselect-wide"
                placeholder="Не указано"
                @input="setEditingDoctor"
              />
            </div>
            <p class="help-block small text-muted">
              Назначается на всю госпитализацию — все дни выбранной записи.
            </p>
          </div>
          <div class="row modal-gender-sick-row">
            <div class="col-xs-6 form-group">
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
            <div class="col-xs-6 form-group modal-sick-col">
              <div class="modal-sick-checkbox-list">
                <div class="checkbox modal-sick-checkbox">
                  <label>
                    <input
                      v-model="editingForm.isNeedSick"
                      type="checkbox"
                    >
                    Больничный
                  </label>
                </div>
                <div
                  v-if="editingRecordPk && !editingStripRowId"
                  class="checkbox modal-sick-checkbox"
                >
                  <label>
                    <input
                      v-model="editingForm.moveToDayDraft"
                      :disabled="!canMoveToDayDraft"
                      :title="moveToDayDraftHint"
                      type="checkbox"
                    >
                    Дневные
                  </label>
                </div>
              </div>
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
  nextTick,
  onBeforeUnmount,
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
  is_need_sick?: boolean;
  is_extract?: boolean;
}

type DischargedPatientRow = {
  key: string;
  directionPk: number;
  name: string;
  dateLabel: string;
};

const STRIP_BOARD_ID = 'strip-board';
const STRIP_BOARD_COLUMNS = 6;
const MAX_CELL_PATIENTS = 2;

const ASIDE_SCROLL_STEP_PX = 56;
const ASIDE_SCROLL_HOLD_MS = 45;
const ASIDE_SCROLL_HOLD_DELAY_MS = 280;

const boardPatientsAside = ref<HTMLElement | null>(null);
const boardAsideViewport = ref<HTMLElement | null>(null);
const boardAsideContent = ref<HTMLElement | null>(null);
const calendarWrapRef = ref<HTMLElement | null>(null);
const boardBodyRef = ref<HTMLElement | null>(null);
const asideScrollOffset = ref(0);
const maxAsideScrollOffset = ref(0);
const calendarBaseHeight = ref(0);

let asideScrollTimer: ReturnType<typeof setInterval> | null = null;
let asideScrollHoldTimer: ReturnType<typeof setTimeout> | null = null;
let asideScrollResizeObserver: ResizeObserver | null = null;

const canAsideScrollUp = computed(() => asideScrollOffset.value > 0);

const asideColumnMinHeightPx = computed(() => {
  const calH = calendarBaseHeight.value;
  if (!calH) {
    return 0;
  }
  const extra = Math.max(0, asideScrollOffset.value - maxAsideScrollOffset.value);
  return calH + extra;
});

const asideColumnStyle = computed(() => {
  const minH = asideColumnMinHeightPx.value;
  if (!minH) {
    return undefined;
  }
  return { minHeight: `${minH}px` };
});

const clampAsideScrollOffset = (value: number) => Math.max(0, value);

const updateAsideScrollBounds = () => {
  const calendar = calendarWrapRef.value;
  const content = boardAsideContent.value;
  if (calendar) {
    calendarBaseHeight.value = calendar.offsetHeight;
  }
  const base = calendarBaseHeight.value;
  if (!content || !base) {
    maxAsideScrollOffset.value = 0;
    return;
  }
  maxAsideScrollOffset.value = Math.max(0, content.offsetHeight - base);
};

const shiftAsideScroll = (delta: number) => {
  updateAsideScrollBounds();
  asideScrollOffset.value = clampAsideScrollOffset(asideScrollOffset.value + delta);
};

const resetAsideScroll = () => {
  asideScrollOffset.value = 0;
};

const stopAsideScrollHold = () => {
  if (asideScrollHoldTimer != null) {
    clearTimeout(asideScrollHoldTimer);
    asideScrollHoldTimer = null;
  }
  if (asideScrollTimer != null) {
    clearInterval(asideScrollTimer);
    asideScrollTimer = null;
  }
};

const startAsideScrollHold = (direction: -1 | 1) => {
  if (direction < 0 && !canAsideScrollUp.value) {
    return;
  }
  shiftAsideScroll(direction * ASIDE_SCROLL_STEP_PX);
  stopAsideScrollHold();
  asideScrollHoldTimer = setTimeout(() => {
    asideScrollTimer = setInterval(() => {
      if (direction < 0 && !canAsideScrollUp.value) {
        stopAsideScrollHold();
        return;
      }
      shiftAsideScroll(direction * ASIDE_SCROLL_STEP_PX);
    }, ASIDE_SCROLL_HOLD_MS);
  }, ASIDE_SCROLL_HOLD_DELAY_MS);
};

const scheduleAsideScrollBoundsUpdate = () => {
  nextTick(() => {
    updateAsideScrollBounds();
  });
};

const stripRecords = ref<CalendarRecord[]>([]);

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const CUSTOM_PERIOD_ACCESS_GROUP = 'Заведующий';
const CUSTOM_PERIOD_MAX_DAYS = 64;

const canUseCustomPeriod = computed(() => (
  (store.getters.user_data?.groups || []).includes(CUSTOM_PERIOD_ACCESS_GROUP)
));

const departments = ref<DepartmentOption[]>([]);
const departmentPk = ref<number | null>(null);
const doctorPk = ref<number>(-1);
const doctors = ref<any[]>([]);
const accompanyingChildOptions = ref<AccompanyingChildOption[]>([]);
const chambers = ref<ChamberData[]>([]);
const records = ref<CalendarRecord[]>([]);
type ExtractDayInfo = {
  count: number;
  directionsList?: number[];
  patientExtractsAdds?: Array<Record<string, string>>;
};
const extractsByDate = ref<Record<string, ExtractDayInfo>>({});
const extractsCount = ref(0);
const extractsDirectionList = ref<number[]>([]);
const defaultHospitalizationPeriodDays = ref(3);
const viewMode = ref<ViewMode>('day');
const anchorDate = ref(moment());
const isCustomPeriodMode = ref(false);
const customPeriodStart = ref('');
const customPeriodEnd = ref('');
const appliedCustomPeriodStart = ref('');
const appliedCustomPeriodEnd = ref('');

const isCustomPeriodActive = computed(() => (
  canUseCustomPeriod.value && isCustomPeriodMode.value
));

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
  isNeedSick: false,
  moveToDayDraft: false,
  commentText: '',
  commentReplicateFollowing: false,
});

const canMoveToDayDraft = computed(() => {
  if (!editingRecordPk.value || editingStripRowId.value) {
    return false;
  }
  const dirTrim = editingForm.value.directionIdText.trim();
  if (!dirTrim) {
    return false;
  }
  const directionPk = Number.parseInt(dirTrim, 10);
  return Number.isFinite(directionPk) && directionPk > 0;
});

const moveToDayDraftHint = computed(() => (
  canMoveToDayDraft.value ? '' : 'Укажите корректный номер направления для переноса в Дневные'
));

const dragOverCellKey = ref('');
const dragOverStripBoard = ref(false);
const dragOverStripRecordPk = ref<number | null>(null);
const hoveredDayKey = ref<string | null>(null);
const suppressCellClick = ref(false);

const isRecordPkOnStrip = (pk: number) => stripRecords.value.some((rec) => rec.pk === pk);

const findStripRecordByPk = (pk: number) => stripRecords.value.find((r) => r.pk === pk) || null;

const unallocatedPatients = ref<UnallocatedPatient[]>([]);
const unallocatedSearch = ref('');
const quickFilterMale = ref(false);
const quickFilterFemale = ref(false);
const quickFilterAccompanying = ref(false);
const quickFilterExtract = ref(false);
const quickFilterSick = ref(false);
const quickFilterFree = ref(false);
const quickFilterClone = ref(false);

const WEEKDAY_SHORT_RU = ['ВС', 'ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ'];

const computeStandardPeriodRange = () => {
  let start = anchorDate.value.clone();
  let end = anchorDate.value.clone();
  if (viewMode.value === 'day') {
    start = anchorDate.value.clone().startOf('day');
    end = anchorDate.value.clone().endOf('day');
  } else if (viewMode.value === 'week') {
    start = anchorDate.value.clone().startOf('isoWeek');
    end = anchorDate.value.clone().endOf('isoWeek');
  } else if (viewMode.value === 'month') {
    start = anchorDate.value.clone().startOf('day');
    end = anchorDate.value.clone().add(31, 'days').endOf('day');
  }
  return { start, end };
};

const buildDayListFromRange = (start: moment.Moment, end: moment.Moment) => {
  const days: Array<{ key: string, label: string }> = [];
  const cursor = start.clone();
  while (cursor.isSameOrBefore(end, 'day')) {
    days.push({
      key: cursor.format('YYYY-MM-DD'),
      label: `${cursor.format('DD.MM')} - ${WEEKDAY_SHORT_RU[cursor.day()]}`,
    });
    cursor.add(1, 'day');
  }
  return days;
};

const customPeriodEndMax = computed(() => {
  if (!customPeriodStart.value) {
    return '';
  }
  const startM = moment(customPeriodStart.value, 'YYYY-MM-DD');
  if (!startM.isValid()) {
    return '';
  }
  return startM.clone().add(CUSTOM_PERIOD_MAX_DAYS - 1, 'days').format('YYYY-MM-DD');
});

const syncCustomPeriodEndConstraints = () => {
  if (!customPeriodStart.value || !customPeriodEnd.value) {
    return;
  }
  const startM = moment(customPeriodStart.value, 'YYYY-MM-DD');
  const endM = moment(customPeriodEnd.value, 'YYYY-MM-DD');
  if (!startM.isValid() || !endM.isValid()) {
    return;
  }
  if (endM.isBefore(startM, 'day')) {
    customPeriodEnd.value = customPeriodStart.value;
    return;
  }
  const maxEnd = startM.clone().add(CUSTOM_PERIOD_MAX_DAYS - 1, 'days');
  if (endM.isAfter(maxEnd, 'day')) {
    customPeriodEnd.value = maxEnd.format('YYYY-MM-DD');
  }
};

const applyCustomPeriodFromDraft = (): boolean => {
  const start = customPeriodStart.value;
  const end = customPeriodEnd.value;
  if (!start || !end) {
    root.$emit('msg', 'error', 'Укажите дату начала и окончания периода');
    return false;
  }
  const startM = moment(start, 'YYYY-MM-DD');
  const endM = moment(end, 'YYYY-MM-DD');
  if (!startM.isValid() || !endM.isValid()) {
    root.$emit('msg', 'error', 'Некорректная дата периода');
    return false;
  }
  if (endM.isBefore(startM, 'day')) {
    root.$emit('msg', 'error', 'Дата окончания не может быть меньше даты начала');
    return false;
  }
  const daysCount = endM.diff(startM, 'days') + 1;
  if (daysCount > CUSTOM_PERIOD_MAX_DAYS) {
    root.$emit('msg', 'error', `Период не может превышать ${CUSTOM_PERIOD_MAX_DAYS} дней`);
    return false;
  }
  appliedCustomPeriodStart.value = start;
  appliedCustomPeriodEnd.value = end;
  return true;
};

const visibleDays = computed(() => {
  if (isCustomPeriodActive.value) {
    if (!appliedCustomPeriodStart.value || !appliedCustomPeriodEnd.value) {
      return [];
    }
    const start = moment(appliedCustomPeriodStart.value, 'YYYY-MM-DD');
    const end = moment(appliedCustomPeriodEnd.value, 'YYYY-MM-DD');
    if (!start.isValid() || !end.isValid() || end.isBefore(start, 'day')) {
      return [];
    }
    return buildDayListFromRange(start, end);
  }
  const { start, end } = computeStandardPeriodRange();
  return buildDayListFromRange(start, end);
});

const todayDayKey = computed(() => moment().format('YYYY-MM-DD'));

const CALENDAR_CHAMBER_COL_WIDTH = 88;
const CALENDAR_BED_COL_WIDTH = 64;
const CALENDAR_DAY_COL_MIN_WIDTH = 108;
const CALENDAR_DAY_COL_MIN_WIDTH_MONTH = 56;

const mainCalendarTableMinWidthPx = computed(() => {
  const dayColWidth = viewMode.value === 'month' && !isCustomPeriodActive.value
    ? CALENDAR_DAY_COL_MIN_WIDTH_MONTH
    : CALENDAR_DAY_COL_MIN_WIDTH;
  return CALENDAR_CHAMBER_COL_WIDTH
    + CALENDAR_BED_COL_WIDTH
    + visibleDays.value.length * dayColWidth;
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

const HOSP_OPEN_END_DAY = '2200-01-01';

const hospUsesPlanCalendar = (rec: CalendarRecord) => Boolean(rec.plan_date_in || rec.plan_date_out);

const hospVisualStart = (rec: CalendarRecord) => moment(rec.plan_date_in || rec.date_in, 'YYYY-MM-DD');

/** При плановых датах конец — plan_date_out, иначе date_out (не min, иначе продление плана не видно). */
const hospVisualEnd = (rec: CalendarRecord) => {
  if (hospUsesPlanCalendar(rec)) {
    if (rec.plan_date_out) {
      return moment(rec.plan_date_out, 'YYYY-MM-DD');
    }
    if (rec.date_out) {
      return moment(rec.date_out, 'YYYY-MM-DD');
    }
    return moment(HOSP_OPEN_END_DAY, 'YYYY-MM-DD');
  }
  if (rec.date_out) {
    return moment(rec.date_out, 'YYYY-MM-DD');
  }
  return moment(HOSP_OPEN_END_DAY, 'YYYY-MM-DD');
};

const isDayInRecordSpan = (rec: CalendarRecord, dayKey: string) => {
  const start = hospVisualStart(rec);
  const d = moment(dayKey, 'YYYY-MM-DD');
  if (!start.isValid() || !d.isValid() || d.isBefore(start, 'day')) {
    return false;
  }
  const end = hospVisualEnd(rec);
  if (!end.isValid()) {
    return true;
  }
  return !d.isAfter(end, 'day');
};

const visiblePeriodBounds = computed(() => {
  const days = visibleDays.value;
  if (!days.length) {
    return null;
  }
  return {
    start: days[0].key,
    end: days[days.length - 1].key,
  };
});

const recordOverlapsVisiblePeriod = (rec: CalendarRecord) => {
  const bounds = visiblePeriodBounds.value;
  if (!bounds) {
    return false;
  }
  const recStart = hospVisualStart(rec).format('YYYY-MM-DD');
  const recEnd = hospVisualEnd(rec).format('YYYY-MM-DD');
  return recStart <= bounds.end && recEnd >= bounds.start;
};

const filterRecordsByDoctor = (list: CalendarRecord[]) => {
  if (doctorPk.value <= 0) {
    return list;
  }
  return list.filter((rec) => rec.doctor_pk === doctorPk.value);
};

const boardSearchQuery = computed(() => unallocatedSearch.value.trim().toLowerCase());

const hasPatientQuickFiltersActive = computed(() => (
  quickFilterMale.value
  || quickFilterFemale.value
  || quickFilterAccompanying.value
  || quickFilterExtract.value
  || quickFilterSick.value
  || quickFilterClone.value
));

const hasActiveBoardQuickFilters = computed(() => (
  hasPatientQuickFiltersActive.value || quickFilterFree.value
));

const hasBoardPatientFilters = computed(() => (
  Boolean(boardSearchQuery.value) || hasActiveBoardQuickFilters.value
));

const textMatchesBoardSearch = (text: string | null | undefined, q: string) => (
  !q || (text || '').toLowerCase().includes(q)
);

const unallocatedMatchesBoardSearch = (p: UnallocatedPatient, q: string) => (
  textMatchesBoardSearch(p.fio, q) || textMatchesBoardSearch(p.short_fio, q)
);

const filterRecordsByBoardSearch = (list: CalendarRecord[]) => {
  const q = boardSearchQuery.value;
  if (!q) {
    return list;
  }
  return list.filter((rec) => textMatchesBoardSearch(rec.patient_fio, q));
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

const isPatientSexMale = (sexRaw: string | null | undefined) => genderColorClass(sexRaw) === 'record-sex--male';

const isPatientSexFemale = (sexRaw: string | null | undefined) => genderColorClass(sexRaw) === 'record-sex--female';

const directionRecordByPk = computed(() => {
  const map = new Map<number, CalendarRecord>();
  for (const rec of records.value) {
    const dirPk = rec.direction_pk;
    if (dirPk != null && dirPk > 0) {
      map.set(dirPk, rec);
    }
  }
  for (const rec of stripRecords.value) {
    const dirPk = rec.direction_pk;
    if (dirPk != null && dirPk > 0 && !map.has(dirPk)) {
      map.set(dirPk, rec);
    }
  }
  return map;
});

const surnameFromFio = (fio: string | null | undefined) => {
  const s = (fio || '').trim();
  if (!s) {
    return '';
  }
  return s.split(/\s+/)[0] || '';
};

const normalizedSurname = (fio: string | null | undefined) => surnameFromFio(fio).toLowerCase().trim();

const duplicateSurnames = computed(() => {
  const counts = new Map<string, number>();
  const appendSurname = (fio: string | null | undefined) => {
    const surname = normalizedSurname(fio);
    if (!surname) {
      return;
    }
    counts.set(surname, (counts.get(surname) || 0) + 1);
  };

  for (const rec of records.value) {
    appendSurname(rec.patient_fio);
  }
  for (const rec of stripRecords.value) {
    appendSurname(rec.patient_fio);
  }
  for (const p of unallocatedPatients.value) {
    appendSurname(p.fio);
  }

  const duplicates = new Set<string>();
  counts.forEach((count, surname) => {
    if (count > 1) {
      duplicates.add(surname);
    }
  });
  return duplicates;
});

const duplicateDirectionPks = computed(() => {
  const counts = new Map<number, number>();
  const appendDirectionPk = (directionPk: number | null | undefined) => {
    if (directionPk == null || directionPk <= 0) {
      return;
    }
    counts.set(directionPk, (counts.get(directionPk) || 0) + 1);
  };

  for (const rec of records.value) {
    appendDirectionPk(rec.direction_pk);
  }
  for (const rec of stripRecords.value) {
    appendDirectionPk(rec.direction_pk);
  }
  for (const p of unallocatedPatients.value) {
    appendDirectionPk(p.direction_pk);
  }

  const duplicates = new Set<number>();
  counts.forEach((count, directionPk) => {
    if (count > 1) {
      duplicates.add(directionPk);
    }
  });
  return duplicates;
});

const isDuplicateBySurnameOrDirection = (fio: string | null | undefined, directionPk: number | null | undefined) => {
  const surname = normalizedSurname(fio);
  const bySurname = Boolean(surname) && duplicateSurnames.value.has(surname);
  const byDirection = directionPk != null && directionPk > 0 && duplicateDirectionPks.value.has(directionPk);
  return bySurname || byDirection;
};

const duplicateColorByGroup = ref(new Map<string, string>());
const duplicateColorIndex = ref(0);

const nextDistinctDuplicateColor = () => {
  const idx = duplicateColorIndex.value;
  duplicateColorIndex.value += 1;
  const hue = (idx * 137.50776405003785) % 360;
  const saturation = 85 - ((idx % 3) * 6);
  const lightness = 48 + ((idx % 2) * 6);
  return `hsla(${hue}, ${saturation}%, ${lightness}%, 0.98)`;
};

const duplicateGroupKey = (fio: string | null | undefined, directionPk: number | null | undefined) => {
  const surname = normalizedSurname(fio);
  const bySurname = Boolean(surname) && duplicateSurnames.value.has(surname);
  const byDirection = directionPk != null && directionPk > 0 && duplicateDirectionPks.value.has(directionPk);
  if (!bySurname && !byDirection) {
    return '';
  }
  if (byDirection) {
    return `d:${directionPk}`;
  }
  return `s:${surname}`;
};

const duplicateColorForGroup = (groupKey: string) => {
  if (!groupKey) {
    return '';
  }
  const existing = duplicateColorByGroup.value.get(groupKey);
  if (existing) {
    return existing;
  }
  const color = nextDistinctDuplicateColor();
  duplicateColorByGroup.value.set(groupKey, color);
  return color;
};

const duplicateHighlightStyle = (fio: string | null | undefined, directionPk: number | null | undefined) => {
  if (!quickFilterClone.value) {
    return {};
  }
  const groupKey = duplicateGroupKey(fio, directionPk);
  if (!groupKey) {
    return {};
  }
  const color = duplicateColorForGroup(groupKey);
  return {
    borderLeft: `8px solid ${color}`,
  };
};

const duplicateHighlightStyleForRecord = (rec: CalendarRecord) => (
  duplicateHighlightStyle(rec.patient_fio, rec.direction_pk)
);

const duplicateHighlightStyleForUnallocated = (p: UnallocatedPatient) => (
  duplicateHighlightStyle(p.fio, p.direction_pk)
);

function calendarRecordMatchesQuickFilters(
  rec: CalendarRecord,
  options?: { treatAsExtract?: boolean },
): boolean {
  if (!hasPatientQuickFiltersActive.value) {
    return true;
  }
  const isExtract = options?.treatAsExtract ?? Boolean(rec.is_extract);

  if (quickFilterMale.value || quickFilterFemale.value) {
    const matchesSex = (quickFilterMale.value && isPatientSexMale(rec.patient_sex))
      || (quickFilterFemale.value && isPatientSexFemale(rec.patient_sex));
    if (!matchesSex) {
      return false;
    }
  }
  if (quickFilterAccompanying.value && !(rec.accompanyng_child_type || '').trim()) {
    return false;
  }
  if (quickFilterExtract.value && !isExtract) {
    return false;
  }
  if (quickFilterSick.value && !rec.is_need_sick) {
    return false;
  }
  if (quickFilterClone.value) {
    if (!isDuplicateBySurnameOrDirection(rec.patient_fio, rec.direction_pk)) {
      return false;
    }
  }
  return true;
}

const filterRecordsByPatientBoardFilters = (list: CalendarRecord[]) => {
  const filtered = filterRecordsByBoardSearch(list);
  if (!hasPatientQuickFiltersActive.value) {
    return filtered;
  }
  return filtered.filter((rec) => calendarRecordMatchesQuickFilters(rec));
};

function unallocatedMatchesQuickFilters(p: UnallocatedPatient): boolean {
  if (!hasPatientQuickFiltersActive.value) {
    return true;
  }
  if (quickFilterMale.value || quickFilterFemale.value) {
    const matchesSex = (quickFilterMale.value && isPatientSexMale(p.sex))
      || (quickFilterFemale.value && isPatientSexFemale(p.sex));
    if (!matchesSex) {
      return false;
    }
  }
  if (quickFilterAccompanying.value || quickFilterExtract.value || quickFilterSick.value) {
    return false;
  }
  if (quickFilterClone.value) {
    if (!isDuplicateBySurnameOrDirection(p.fio, p.direction_pk)) {
      return false;
    }
  }
  return true;
}

function dischargedRowMatchesQuickFilters(row: DischargedPatientRow): boolean {
  if (!hasActiveBoardQuickFilters.value) {
    return true;
  }
  if (quickFilterFree.value) {
    return false;
  }
  const rec = directionRecordByPk.value.get(row.directionPk);
  if (!rec) {
    return quickFilterExtract.value
      && !quickFilterMale.value
      && !quickFilterFemale.value
      && !quickFilterAccompanying.value
      && !quickFilterSick.value
      && !quickFilterClone.value;
  }
  return calendarRecordMatchesQuickFilters(rec, { treatAsExtract: true });
}

const stripRecordsInPeriod = computed(() => {
  const byPeriod = stripRecords.value.filter(recordOverlapsVisiblePeriod);
  return filterRecordsByPatientBoardFilters(filterRecordsByDoctor(byPeriod));
});

const stripRecordsInPeriodNotExtractCount = computed(() => (
  stripRecordsInPeriod.value.filter((rec) => !rec.is_extract).length
));

const stripNeedsExtraDropRow = computed(() => {
  const count = stripRecordsInPeriod.value.length;
  return count === 0 || count % STRIP_BOARD_COLUMNS === 0;
});

const stripDefaultDayKey = computed(() => {
  const days = visibleDays.value;
  if (!days.length) {
    return todayDayKey.value;
  }
  const today = todayDayKey.value;
  if (days.some((d) => d.key === today)) {
    return today;
  }
  return days[0].key;
});

const formatDayShort = (dayKey: string | null | undefined) => {
  if (!dayKey) {
    return '';
  }
  const m = moment(dayKey, 'YYYY-MM-DD', true);
  return m.isValid() ? m.format('DD.MM') : '';
};

const formatStripPeriodLabel = (rec: CalendarRecord) => {
  const start = formatDayShort(rec.plan_date_in || rec.date_in);
  const end = formatDayShort(rec.plan_date_out || rec.date_out);
  if (start && end) {
    return start === end ? start : `${start}-${end}`;
  }
  if (start) {
    return `с ${start}`;
  }
  if (end) {
    return `до ${end}`;
  }
  return '';
};

const stripRecordPkSet = computed(() => new Set(stripRecords.value.map((rec) => rec.pk)));

const stripDirectionPkSet = computed(() => {
  const s = new Set<number>();
  for (const rec of stripRecords.value) {
    const dirPk = rec.direction_pk;
    if (dirPk != null && dirPk > 0) {
      s.add(dirPk);
    }
  }
  return s;
});

const placedDirectionPkSet = computed(() => {
  const s = new Set<number>(stripDirectionPkSet.value);
  for (const rec of records.value) {
    const dirPk = rec.direction_pk;
    if (dirPk != null && dirPk > 0) {
      s.add(dirPk);
    }
  }
  return s;
});

const removeUnallocatedPatientByDirection = (directionPk: number) => {
  if (!Number.isFinite(directionPk) || directionPk <= 0) {
    return;
  }
  unallocatedPatients.value = unallocatedPatients.value.filter(
    (p) => p.direction_pk !== directionPk,
  );
};

const recordsUnfilteredForMainGrid = computed(() => (
  records.value.filter((r) => !stripRecordPkSet.value.has(r.pk))
));

const recordsForMainGrid = computed(() => {
  const byDoctor = filterRecordsByDoctor(recordsUnfilteredForMainGrid.value);
  return filterRecordsByPatientBoardFilters(byDoctor);
});

const recordsByBedAndDay = computed(() => {
  const map = new Map<string, CalendarRecord[]>();
  const days = visibleDays.value;
  if (!days.length) {
    return map;
  }
  for (const record of recordsForMainGrid.value) {
    const start = hospVisualStart(record);
    if (!start.isValid()) {
      continue;
    }
    for (const { key: dayKey } of days) {
      if (!isDayInRecordSpan(record, dayKey)) {
        continue;
      }
      const key = `${record.bed_pk}-${dayKey}`;
      const list = map.get(key) || [];
      list.push(record);
      map.set(key, list);
    }
  }
  return map;
});

const cellRecordList = (bedPk: number, dayKey: string): CalendarRecord[] => {
  const list = recordsByBedAndDay.value.get(`${bedPk}-${dayKey}`) || [];
  return [...list].sort((a, b) => {
    if (Boolean(a.is_extract) === Boolean(b.is_extract)) {
      return 0;
    }
    return a.is_extract ? -1 : 1;
  });
};

const isRecordDischargeDay = (rec: CalendarRecord, dayKey: string) => {
  if (!rec.is_extract) {
    return false;
  }
  const end = hospVisualEnd(rec);
  const d = moment(dayKey, 'YYYY-MM-DD');
  return end.isValid() && d.isValid() && end.isSame(d, 'day');
};

const getRecordForDay = (bedPk: number, dayKey: string) => {
  const list = cellRecordList(bedPk, dayKey);
  return list.find((r) => !r.is_extract) || list[0];
};

const bedPeriodHasOverlap = (
  bedPk: number,
  planDateIn: string | null | undefined,
  planDateOut: string | null | undefined,
  excludeRecordPk?: number | null,
) => {
  const from = moment(planDateIn, 'YYYY-MM-DD');
  if (!from.isValid()) {
    return false;
  }
  const to = planDateOut
    ? moment(planDateOut, 'YYYY-MM-DD')
    : moment(HOSP_OPEN_END_DAY, 'YYYY-MM-DD');
  if (!to.isValid() || from.isAfter(to, 'day')) {
    return false;
  }
  for (const rec of recordsUnfilteredForMainGrid.value) {
    if (excludeRecordPk != null && rec.pk === excludeRecordPk) {
      continue;
    }
    if (rec.bed_pk !== bedPk) {
      continue;
    }
    const recStart = hospVisualStart(rec);
    if (!recStart.isValid()) {
      continue;
    }
    const recEnd = hospVisualEnd(rec);
    if (from.isSameOrBefore(recEnd, 'day') && to.isSameOrAfter(recStart, 'day')) {
      if (rec.is_extract && from.isSame(recEnd, 'day')) {
        continue;
      }
      return true;
    }
  }
  return false;
};

const assertNoBedPeriodOverlap = (
  bedPk: number,
  planDateIn: string | null | undefined,
  planDateOut: string | null | undefined,
  excludeRecordPk?: number | null,
) => {
  if (!bedPeriodHasOverlap(bedPk, planDateIn, planDateOut, excludeRecordPk)) {
    return true;
  }
  root.$emit('msg', 'error', 'На этой койке период пересекается с другой госпитализацией');
  return false;
};

/** Записи на койке в этот день (без фильтра врача — для проверки занятости при drop). */
const bedDayOccupyingRecords = (bedPk: number, dayKey: string) => (
  recordsUnfilteredForMainGrid.value.filter(
    (r) => r.bed_pk === bedPk && isDayInRecordSpan(r, dayKey),
  )
);

/** Койка свободна: пустая или только выписанный в день выписки (без второго пациента). */
const isBedFreeForOccupying = (occupying: CalendarRecord[], dayKey: string) => {
  if (occupying.length === 0) {
    return true;
  }
  if (occupying.length > 1) {
    return false;
  }
  const only = occupying[0];
  return Boolean(only.is_extract && isRecordDischargeDay(only, dayKey));
};

const isBedFreeForDay = (bedPk: number, dayKey: string) => (
  isBedFreeForOccupying(bedDayOccupyingRecords(bedPk, dayKey), dayKey)
);

const bedHasFreeDayInPeriod = (bedPk: number) => {
  for (const day of visibleDays.value) {
    if (isBedFreeForDay(bedPk, day.key)) {
      return true;
    }
  }
  return false;
};

/** При поиске/фильтрах — только подходящие койки (сжатие таблицы). */
const chamberRowsForDisplay = computed(() => {
  if (!hasBoardPatientFilters.value) {
    return chamberRows.value;
  }
  const matchBedPks = new Set<number>();
  const filterByPatientRecords = boardSearchQuery.value || hasPatientQuickFiltersActive.value;
  if (filterByPatientRecords) {
    for (const rec of recordsForMainGrid.value) {
      if (rec.bed_pk > 0 && recordOverlapsVisiblePeriod(rec)) {
        matchBedPks.add(rec.bed_pk);
      }
    }
  }
  if (quickFilterFree.value) {
    for (const row of chamberRows.value) {
      for (const bed of row.beds) {
        if (bedHasFreeDayInPeriod(bed.pk)) {
          matchBedPks.add(bed.pk);
        }
      }
    }
  }
  if (!matchBedPks.size) {
    return [];
  }
  const requirePatientBeds = filterByPatientRecords;
  const requireFreeBeds = quickFilterFree.value;
  return chamberRows.value
    .map((row) => ({
      ...row,
      beds: row.beds.filter((b) => {
        if (!matchBedPks.has(b.pk)) {
          return false;
        }
        if (requirePatientBeds && requireFreeBeds) {
          const hasPatient = recordsForMainGrid.value.some(
            (rec) => rec.bed_pk === b.pk && recordOverlapsVisiblePeriod(rec),
          );
          return hasPatient && bedHasFreeDayInPeriod(b.pk);
        }
        return true;
      }),
    }))
    .filter((row) => row.beds.length > 0);
});

const canAcceptPatientInCell = (
  bedPk: number,
  dayKey: string,
  excludeDirectionPk?: number | null,
) => {
  let occupying = bedDayOccupyingRecords(bedPk, dayKey);
  if (excludeDirectionPk != null) {
    occupying = occupying.filter((r) => r.direction_pk !== excludeDirectionPk);
  }
  if (occupying.length >= MAX_CELL_PATIENTS) {
    return false;
  }
  return isBedFreeForOccupying(occupying, dayKey);
};

const assertCanAcceptPatientInCell = (
  bedPk: number,
  dayKey: string,
  excludeDirectionPk?: number | null,
) => {
  if (canAcceptPatientInCell(bedPk, dayKey, excludeDirectionPk)) {
    return true;
  }
  const occupying = bedDayOccupyingRecords(bedPk, dayKey).filter(
    (r) => excludeDirectionPk == null || r.direction_pk !== excludeDirectionPk,
  );
  if (occupying.length >= MAX_CELL_PATIENTS) {
    root.$emit('msg', 'error', 'В ячейке уже два пациента — допустимы только выписанный и новый');
    return false;
  }
  root.$emit('msg', 'error', 'На этой койке уже есть госпитализация на выбранную дату');
  return false;
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
  const fio = (rec.patient_fio || '').trim();
  const dateLabel = formatDayShort(dayKey);
  let title = '';
  if (fio && dateLabel) {
    title = `${fio} (${dateLabel})`;
  } else {
    title = fio || (dateLabel ? `(${dateLabel})` : '');
  }
  if (rec.is_extract) {
    const dischargeEnd = hospVisualEnd(rec);
    const dischargeLabel = dischargeEnd.isValid()
      ? formatDayShort(dischargeEnd.format('YYYY-MM-DD'))
      : '';
    if (dischargeLabel) {
      title = title ? `${title}, выписан ${dischargeLabel}` : `выписан ${dischargeLabel}`;
    } else {
      title = title ? `${title}, выписан` : 'выписан';
    }
  }
  return title;
};

const formatCellDoctorSurname = (record: CalendarRecord) => surnameFromFio(record.doctor_fio);

const CELL_COMMENT_DISPLAY_MAX = 45;
const CELL_COMMENT_DISPLAY_MAX_MONTH = 22;

const cellCommentAfterDoctor = (record: CalendarRecord, dayKey: string) => {
  const raw = commentForRecordDay(record, dayKey).trim();
  if (!raw) {
    return '';
  }
  const max = viewMode.value === 'month' && !isCustomPeriodActive.value
    ? CELL_COMMENT_DISPLAY_MAX_MONTH
    : CELL_COMMENT_DISPLAY_MAX;
  if (raw.length <= max) {
    return raw;
  }
  return `${raw.slice(0, max)}…`;
};

/** Как в ManageChambers / DirectionsHistory: hash с JSON для экрана стационара */
const stationarHref = (directionPk: number) => (
  `/ui/stationar#{%22pk%22:${directionPk},%22opened_list_key%22:null,%22opened_form_pk%22:null,%22every%22:false}`
);

const accompanyingDisplayLetter = (record: CalendarRecord) => {
  const t = (record.accompanyng_child_type || '').trim();
  if (!t) {
    return '';
  }
  return t.charAt(0).toLocaleUpperCase('ru-RU');
};

const isTodayDayColumn = (dayKey: string) => dayKey === todayDayKey.value;

type DayColumnTotals = { male: number, female: number, accompanying: number, free: number };

const emptyDayColumnTotals = (): DayColumnTotals => ({
  male: 0,
  female: 0,
  accompanying: 0,
  free: 0,
});

const calendarBedPks = computed(() => {
  const pks: number[] = [];
  for (const row of chamberRows.value) {
    for (const bed of row.beds) {
      pks.push(bed.pk);
    }
  }
  return pks;
});

const applyExtractsFromResponse = (extracts: Record<string, unknown> | null | undefined) => {
  const raw = extracts || {};
  const total = Number(raw.count);
  extractsCount.value = Number.isFinite(total) ? total : 0;
  const dirList = raw.directionList;
  extractsDirectionList.value = Array.isArray(dirList)
    ? dirList.map((id) => Number(id)).filter((id) => Number.isFinite(id))
    : [];
  const byDate: Record<string, ExtractDayInfo> = {};
  Object.entries(raw).forEach(([key, value]) => {
    if (key === 'count' || key === 'directionList' || !value || typeof value !== 'object') {
      return;
    }
    const item = value as ExtractDayInfo;
    if (Number.isFinite(Number(item.count))) {
      byDate[key] = item;
    }
  });
  extractsByDate.value = byDate;
};

const openExtractsDetailForm = () => {
  if (!extractsDirectionList.value.length) {
    root.$emit('msg', 'error', 'Нет выписок за выбранный период');
    return;
  }
  if (!departmentPk.value) {
    root.$emit('msg', 'error', 'Не выбрано подразделение');
    return;
  }
  if (visibleDays.value.length === 0) {
    root.$emit('msg', 'error', 'Не задан период');
    return;
  }
  const startDate = visibleDays.value[0].key;
  const endDate = visibleDays.value[visibleDays.value.length - 1].key;
  const params = new URLSearchParams({
    type: '105.01',
    department_pk: String(departmentPk.value),
    start_date: startDate,
    end_date: endDate,
    direction_list: JSON.stringify(extractsDirectionList.value),
  });
  window.open(`/forms/xlsx?${params.toString()}`, '_blank');
};

const extractDateKeyFromDayKey = (dayKey: string) => moment(dayKey, 'YYYY-MM-DD').format('DD.MM.YY');

const parseExtractAddsEntry = (entry: Record<string, string>) => {
  const keys = Object.keys(entry);
  if (!keys.length) {
    return null;
  }
  const directionPk = Number(keys[0]);
  const name = (entry[keys[0]] || '').trim();
  if (!Number.isFinite(directionPk) || directionPk <= 0 || !name) {
    return null;
  }
  return { directionPk, name };
};

const dischargedPatientsInPeriodAll = computed(() => {
  const rows: DischargedPatientRow[] = [];
  for (const day of visibleDays.value) {
    const extractKey = extractDateKeyFromDayKey(day.key);
    const adds = extractsByDate.value[extractKey]?.patientExtractsAdds;
    if (!adds?.length) {
      continue;
    }
    adds.forEach((entry, idx) => {
      const parsed = parseExtractAddsEntry(entry);
      if (!parsed) {
        return;
      }
      rows.push({
        key: `${day.key}-${parsed.directionPk}-${idx}`,
        directionPk: parsed.directionPk,
        name: parsed.name,
        dateLabel: day.label,
      });
    });
  }
  return rows;
});

const extractCountForDay = (dayKey: string) => {
  let count = 0;
  for (const rec of recordsUnfilteredForMainGrid.value) {
    if (isRecordDischargeDay(rec, dayKey)) {
      count += 1;
    }
  }
  for (const rec of stripRecords.value) {
    if (isRecordDischargeDay(rec, dayKey)) {
      count += 1;
    }
  }
  return count;
};

const dischargedPatientsInPeriod = computed(() => {
  let list = dischargedPatientsInPeriodAll.value;
  const q = boardSearchQuery.value;
  if (q) {
    list = list.filter((row) => textMatchesBoardSearch(row.name, q));
  }
  if (!hasActiveBoardQuickFilters.value) {
    return list;
  }
  return list.filter((row) => dischargedRowMatchesQuickFilters(row));
});

const hasDischargedInPeriod = computed(() => dischargedPatientsInPeriodAll.value.length > 0);

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
      if (isRecordDischargeDay(rec, day.key)) {
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
  for (const day of visibleDays.value) {
    const t = map.get(day.key) || emptyDayColumnTotals();
    let free = 0;
    for (const bedPk of calendarBedPks.value) {
      if (isBedFreeForDay(bedPk, day.key)) {
        free += 1;
      }
    }
    t.free = free;
    map.set(day.key, t);
  }
  return map;
});

const dayColumnTotals = (dayKey: string): DayColumnTotals => (
  dayColumnTotalsMap.value.get(dayKey) || emptyDayColumnTotals()
);

const uniqueRecordKey = (rec: CalendarRecord) => (
  rec.direction_pk != null && rec.direction_pk > 0
    ? `d:${rec.direction_pk}`
    : `r:${rec.pk}`
);

/** Есть хотя бы один день в периоде, когда запись занимает койку (не только день выписки). */
const recordHasOccupiedDayInPeriod = (rec: CalendarRecord) => {
  for (const day of visibleDays.value) {
    if (!isDayInRecordSpan(rec, day.key)) {
      continue;
    }
    if (isRecordDischargeDay(rec, day.key)) {
      continue;
    }
    return true;
  }
  return false;
};

const periodMainGridRecordsForCounts = computed(() => (
  filterRecordsByDoctor(recordsUnfilteredForMainGrid.value).filter(recordOverlapsVisiblePeriod)
));

type QuickFilterCountPart = { key: string, label: string };

/** Уникальные записи/койки за период по включённым быстрым фильтрам (как счётчики в шапке даты). */
const quickFilterPeriodCountParts = computed((): QuickFilterCountPart[] => {
  if (!hasActiveBoardQuickFilters.value) {
    return [];
  }
  const parts: QuickFilterCountPart[] = [];
  const main = periodMainGridRecordsForCounts.value;

  const countUniqueRecords = (
    list: CalendarRecord[],
    predicate: (rec: CalendarRecord) => boolean,
  ) => {
    const keys = new Set<string>();
    for (const rec of list) {
      if (!predicate(rec)) {
        continue;
      }
      keys.add(uniqueRecordKey(rec));
    }
    return keys.size;
  };

  if (quickFilterMale.value) {
    parts.push({
      key: 'male',
      label: `М ${countUniqueRecords(main, (rec) => (
        isPatientSexMale(rec.patient_sex) && recordHasOccupiedDayInPeriod(rec)
      ))}`,
    });
  }
  if (quickFilterFemale.value) {
    parts.push({
      key: 'female',
      label: `Ж ${countUniqueRecords(main, (rec) => (
        isPatientSexFemale(rec.patient_sex) && recordHasOccupiedDayInPeriod(rec)
      ))}`,
    });
  }
  if (quickFilterAccompanying.value) {
    parts.push({
      key: 'accompanying',
      label: `С ${countUniqueRecords(main, (rec) => (
        Boolean((rec.accompanyng_child_type || '').trim()) && recordHasOccupiedDayInPeriod(rec)
      ))}`,
    });
  }
  if (quickFilterExtract.value) {
    const extractKeys = new Set<string>();
    const extractLists = [
      filterRecordsByDoctor(recordsUnfilteredForMainGrid.value),
      filterRecordsByDoctor(stripRecords.value),
    ];
    for (const list of extractLists) {
      for (const rec of list) {
        for (const day of visibleDays.value) {
          if (isRecordDischargeDay(rec, day.key)) {
            extractKeys.add(uniqueRecordKey(rec));
            break;
          }
        }
      }
    }
    parts.push({ key: 'extract', label: `В ${extractKeys.size}` });
  }
  if (quickFilterFree.value) {
    let freeBeds = 0;
    for (const bedPk of calendarBedPks.value) {
      if (bedHasFreeDayInPeriod(bedPk)) {
        freeBeds += 1;
      }
    }
    parts.push({ key: 'free', label: `Н ${freeBeds}` });
  }
  if (quickFilterSick.value) {
    parts.push({
      key: 'sick',
      label: `Б ${countUniqueRecords(main, (rec) => (
        Boolean(rec.is_need_sick) && recordOverlapsVisiblePeriod(rec)
      ))}`,
    });
  }
  return parts;
});

const quickFilterPeriodCountSummary = computed(() => (
  quickFilterPeriodCountParts.value.map((part) => part.label).join(' · ')
));

/** День для счётчика на бейджах врачей: наведённая колонка, иначе «День» / сегодня */
const doctorBadgeCountDayKey = computed(() => {
  if (hoveredDayKey.value) {
    return hoveredDayKey.value;
  }
  if (isCustomPeriodActive.value) {
    const days = visibleDays.value;
    return days[0]?.key || todayDayKey.value;
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
  for (const rec of stripRecords.value) {
    addDoctorPatientCountForRecord(map, rec, dayKey);
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

const applyDefaultDepartmentFromProfile = () => {
  if (departmentPk.value != null) {
    return;
  }
  const userDepartmentPk = Number(store.getters.user_data?.department?.pk);
  if (!Number.isFinite(userDepartmentPk) || userDepartmentPk <= 0) {
    return;
  }
  const userDepartment = departments.value.find((d) => d.id === userDepartmentPk);
  if (userDepartment) {
    departmentPk.value = userDepartment.id;
  }
};

const loadDepartments = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { data } = await api('procedural-list/suitable-departments');
  await store.dispatch(actions.DEC_LOADING);
  departments.value = data;
  applyDefaultDepartmentFromProfile();
};

const loadAccompanyingChildOptions = async () => {
  await store.dispatch(actions.INC_LOADING);
  const res = await api('chambers/get-accompanying-child-options');
  await store.dispatch(actions.DEC_LOADING);
  const list = res?.data;
  accompanyingChildOptions.value = Array.isArray(list) ? list : [];
};

const loadDoctors = async () => {
  if (!departmentPk.value) {
    doctors.value = [];
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const response = await api('chambers/get-attending-doctors', {
    department_pk: departmentPk.value,
    only_stationar_role: true,
  });
  await store.dispatch(actions.DEC_LOADING);
  doctors.value = response.data || [];
};

const loadUnallocatedPatients = async () => {
  if (!departmentPk.value) {
    unallocatedPatients.value = [];
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const row = await api('chambers/get-unallocated-patients', {
    department_pk: departmentPk.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  unallocatedPatients.value = Array.isArray(row.data) ? row.data : [];
};

const defaultPlanDateOut = (dayKey: string) => {
  const days = defaultHospitalizationPeriodDays.value;
  return moment(dayKey, 'YYYY-MM-DD').add(days - 1, 'days').format('YYYY-MM-DD');
};

const doctorFioByPk = (docPk: number) => {
  const d = doctors.value.find((x) => x.pk === docPk);
  return (d?.short_fio || d?.fio || '').trim();
};

const attendingDoctorTreeselectOptions = computed(() => (
  doctors.value.map((doctor) => ({
    id: doctor.pk,
    label: doctor.short_fio || doctor.fio || String(doctor.pk),
  }))
));

type StripServerPatient = {
  direction_pk: number;
  fio: string;
  sex: string;
  age: number;
  doctor_pk?: number | null;
  is_extract?: boolean;
  date_in?: string | null;
  date_out?: string | null;
  plan_date_in?: string | null;
  plan_date_out?: string | null;
};

const applyStripHospMeta = (
  rec: CalendarRecord,
  meta: Partial<StripServerPatient> & { direction_pk?: number },
): CalendarRecord => {
  const next = { ...rec };
  if (meta.is_extract != null) {
    next.is_extract = Boolean(meta.is_extract);
  }
  if (meta.date_in) {
    next.date_in = meta.date_in;
  }
  if (meta.plan_date_in) {
    next.plan_date_in = meta.plan_date_in;
  }
  if (meta.plan_date_out) {
    next.plan_date_out = meta.plan_date_out;
  }
  if (meta.date_out != null) {
    next.date_out = meta.date_out;
  } else if (meta.plan_date_out) {
    next.date_out = meta.plan_date_out;
  }
  return next;
};

const saveStripPatientToServer = async (rec: CalendarRecord) => {
  if (!departmentPk.value || !rec.direction_pk) {
    return null;
  }
  await store.dispatch(actions.INC_LOADING);
  const result = await api('chambers/save-patient-without-bed', {
    department_pk: departmentPk.value,
    patient_obj: { direction_pk: rec.direction_pk },
    doctor_id: rec.doctor_pk ?? null,
    plan_date_in: rec.plan_date_in,
    plan_date_out: rec.plan_date_out,
    date_out: rec.date_out,
    is_extract: Boolean(rec.is_extract),
  });
  await store.dispatch(actions.DEC_LOADING);
  return result;
};

const newStripRecordFromServerPatient = (
  p: StripServerPatient,
  dayKey: string,
): CalendarRecord => {
  const planIn = p.plan_date_in || p.date_in || dayKey;
  const planOut = p.plan_date_out || p.date_out || defaultPlanDateOut(planIn);
  const rec: CalendarRecord = {
    pk: -p.direction_pk,
    bed_pk: 0,
    doctor_pk: p.doctor_pk ?? null,
    doctor_fio: p.doctor_pk ? doctorFioByPk(p.doctor_pk) : '',
    patient_fio: p.fio,
    patient_sex: p.sex || 'м',
    birthday: null,
    patient_age_text: String(p.age ?? ''),
    direction_pk: p.direction_pk,
    date_in: p.date_in || planIn,
    date_out: p.date_out || null,
    plan_date_in: planIn,
    plan_date_out: planOut,
    accompanyng_child_type: '',
    accompanyng_child_sex: '-',
    date_comments: {},
    is_day_hosp: true,
    is_need_sick: false,
    is_extract: Boolean(p.is_extract),
  };
  return applyStripHospMeta(rec, p);
};

const syncStripRecordsDischargeMeta = async () => {
  if (!departmentPk.value) {
    return;
  }
  const directionPks = new Set<number>();
  for (const rec of stripRecords.value) {
    if (rec.direction_pk != null && rec.direction_pk > 0) {
      directionPks.add(rec.direction_pk);
    }
  }
  if (!directionPks.size) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const res = await api('chambers/get-directions-hosp-meta', {
    direction_pks: [...directionPks],
  });
  await store.dispatch(actions.DEC_LOADING);
  const items = Array.isArray(res?.data) ? res.data : [];
  const byDir = new Map<number, StripServerPatient>();
  for (const item of items) {
    const pk = Number(item?.direction_pk);
    if (Number.isFinite(pk) && pk > 0) {
      byDir.set(pk, item);
    }
  }
  for (const rec of stripRecords.value) {
    const dirPk = rec.direction_pk;
    if (dirPk != null && dirPk > 0 && byDir.has(dirPk)) {
      Object.assign(rec, applyStripHospMeta(rec, byDir.get(dirPk)!));
    }
  }
};

const loadPatientsWithoutBed = async () => {
  if (!departmentPk.value) {
    stripRecords.value = [];
    return;
  }
  const bounds = visiblePeriodBounds.value;
  if (!bounds) {
    stripRecords.value = [];
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const row = await api('chambers/get-patients-without-bed', {
    department_pk: departmentPk.value,
    start_date: bounds.start,
    end_date: bounds.end,
  });
  await store.dispatch(actions.DEC_LOADING);
  const list = Array.isArray(row?.data) ? row.data : [];
  const dayKey = stripDefaultDayKey.value;
  stripRecords.value = list
    .filter((p: any) => Number.isFinite(Number(p?.direction_pk)) && Number(p.direction_pk) > 0)
    .map((p: any) => newStripRecordFromServerPatient({
      direction_pk: Number(p.direction_pk),
      fio: String(p.fio || ''),
      sex: String(p.sex || 'м'),
      age: Number(p.age ?? ''),
      doctor_pk: p.doctor_pk != null ? Number(p.doctor_pk) : null,
      is_extract: Boolean(p.is_extract),
      date_in: p.date_in || null,
      date_out: p.date_out || null,
      plan_date_in: p.plan_date_in || null,
      plan_date_out: p.plan_date_out || null,
    }, dayKey));
};

const reloadStripFromServer = async () => {
  await loadPatientsWithoutBed();
  await syncStripRecordsDischargeMeta();
};

const removeStripRecordPk = async (pk: number) => {
  const rec = findStripRecordByPk(pk);
  if (departmentPk.value && rec?.direction_pk) {
    await store.dispatch(actions.INC_LOADING);
    const res = await api('chambers/delete-patient-without-bed', {
      department_pk: departmentPk.value,
      patient_obj: { direction_pk: rec.direction_pk },
    });
    await store.dispatch(actions.DEC_LOADING);
    if (!res?.ok) {
      root.$emit('msg', 'error', res?.message || 'Не удалось удалить черновик на сервере');
      return false;
    }
  }
  stripRecords.value = stripRecords.value.filter((r) => r.pk !== pk);
  await reloadStripFromServer();
  return true;
};

const unallocatedPatientsFiltered = computed(() => {
  let list = unallocatedPatients.value.filter(
    (p) => !placedDirectionPkSet.value.has(p.direction_pk),
  );
  const q = boardSearchQuery.value;
  if (q) {
    list = list.filter((p) => unallocatedMatchesBoardSearch(p, q));
  }
  if (!hasPatientQuickFiltersActive.value) {
    return list;
  }
  return list.filter((p) => unallocatedMatchesQuickFilters(p));
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
    view_mode: isCustomPeriodActive.value ? 'custom' : viewMode.value,
  });
  chambers.value = response?.data?.chambers || [];
  records.value = response?.data?.records || [];
  applyExtractsFromResponse(response?.data?.extracts);
  const periodDays = Number(response?.data?.default_period_days);
  defaultHospitalizationPeriodDays.value = Number.isFinite(periodDays) && periodDays >= 1
    ? periodDays
    : 3;
  await store.dispatch(actions.DEC_LOADING);
};

const refreshBoard = async () => {
  if (isCustomPeriodActive.value && !applyCustomPeriodFromDraft()) {
    return;
  }
  await loadCalendar();
  await loadUnallocatedPatients();
  await reloadStripFromServer();
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
  dragOverStripBoard.value = false;
  dragOverStripRecordPk.value = null;
};

const onDoctorStripCardDrop = async (rec: CalendarRecord, docPk: number) => {
  const updated = {
    ...rec,
    doctor_pk: docPk,
    doctor_fio: doctorFioByPk(docPk),
  };
  const res = await saveStripPatientToServer(updated);
  if (!res?.ok) {
    root.$emit('msg', 'error', res?.message || 'Не удалось сохранить черновик на сервере');
    return;
  }
  await reloadStripFromServer();
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

const onStripPatientDragStart = (e: DragEvent, rec: CalendarRecord) => {
  e.stopPropagation();
  e.dataTransfer?.setData('application/x-l2-strip-record-pk', String(rec.pk));
  e.dataTransfer?.setData('text/plain', `strip-record:${rec.pk}`);
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
  }
};

const onPatientDragEnd = () => {
  dragOverCellKey.value = '';
  dragOverStripBoard.value = false;
  dragOverStripRecordPk.value = null;
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

const onStripBoardDragOver = () => {
  dragOverStripBoard.value = true;
};

const onStripBoardDragLeave = (e: DragEvent) => {
  const current = e.currentTarget as Node | null;
  const related = e.relatedTarget as Node | null;
  if (current && related && current.contains(related)) {
    return;
  }
  dragOverStripBoard.value = false;
};

const onStripCardDragOver = (rec: CalendarRecord) => {
  dragOverStripRecordPk.value = rec.pk;
};

const onStripCardDragLeave = (e: DragEvent, rec: CalendarRecord) => {
  const current = e.currentTarget as Node | null;
  const related = e.relatedTarget as Node | null;
  if (current && related && current.contains(related)) {
    return;
  }
  if (dragOverStripRecordPk.value === rec.pk) {
    dragOverStripRecordPk.value = null;
  }
};

const onStripCardDrop = async (e: DragEvent, rec: CalendarRecord) => {
  dragOverStripRecordPk.value = null;
  const docFromMime = e.dataTransfer?.getData('application/x-l2-doctor-pk') || '';
  const plain = e.dataTransfer?.getData('text/plain') || '';
  const docRaw = docFromMime || (plain.startsWith('hosp-move:') || plain.startsWith('strip-record:') ? '' : plain);
  if (!docRaw || docRaw.startsWith('hosp-move:') || docRaw.startsWith('strip-record:')) {
    return;
  }
  const docPk = Number.parseInt(docRaw, 10);
  if (Number.isNaN(docPk)) {
    return;
  }
  await onDoctorStripCardDrop(rec, docPk);
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
    is_day_hosp: true,
    is_need_sick: false,
  };
};

const onUnallocatedToStripDrop = async (dayKey: string, raw: string) => {
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
  const res = await saveStripPatientToServer(record);
  if (!res?.ok) {
    root.$emit('msg', 'error', res?.message || 'Не удалось сохранить черновик на сервере');
    return;
  }
  removeUnallocatedPatientByDirection(directionPk);
  await reloadStripFromServer();
  await loadUnallocatedPatients();
  root.$emit('msg', 'ok', 'Пациент добавлен в черновик');
};

const onStripBoardDrop = async (e: DragEvent) => {
  dragOverStripBoard.value = false;
  const dayKey = stripDefaultDayKey.value;
  const panelDir = e.dataTransfer?.getData(DND_UNALLOCATED_DIRECTION);
  if (panelDir) {
    await onUnallocatedToStripDrop(dayKey, panelDir);
    return;
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
  if (!recordOverlapsVisiblePeriod(rec)) {
    root.$emit('msg', 'error', 'Пациент вне выбранного периода');
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
  if (!okClear) {
    await store.dispatch(actions.DEC_LOADING);
    root.$emit('msg', 'error', msgClear || 'Не удалось освободить койку');
    return;
  }
  const stripRec = {
    ...rec,
    is_extract: Boolean(rec.is_extract),
  };
  const saveRes = await saveStripPatientToServer(stripRec);
  if (!saveRes?.ok) {
    await store.dispatch(actions.DEC_LOADING);
    root.$emit('msg', 'error', saveRes?.message || 'Не удалось сохранить черновик на сервере');
    return;
  }
  await loadCalendar();
  await reloadStripFromServer();
  await store.dispatch(actions.DEC_LOADING);
  root.$emit('msg', 'ok', 'Пациент перенесён в черновик');
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
  dragOverStripBoard.value = false;
  dragOverStripRecordPk.value = null;
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
    if (!(await removeStripRecordPk(recordPk))) {
      return;
    }
    await loadCalendar();
    return;
  }
  const movePlanIn = targetDayKey;
  const movePlanOut = sourceRec.plan_date_out || sourceRec.date_out || null;
  if (!assertCanAcceptPatientInCell(targetBedPk, targetDayKey, sourceRec.direction_pk)) {
    return;
  }
  if (!assertNoBedPeriodOverlap(targetBedPk, movePlanIn, movePlanOut, sourceRec.pk)) {
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
    if (fromStrip && !(await removeStripRecordPk(recordPk))) {
      return;
    }
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
  stripRecordPkRaw?: string,
) => {
  if (!departmentPk.value) {
    return;
  }
  let record: CalendarRecord | null = null;
  if (stripRecordPkRaw) {
    const stripRecordPk = Number.parseInt(stripRecordPkRaw, 10);
    if (!Number.isNaN(stripRecordPk)) {
      record = findStripRecordByPk(stripRecordPk);
    }
  }
  if (!record) {
    root.$emit('msg', 'error', 'Запись в черновике не найдена');
    return;
  }
  if (!isDayInRecordSpan(record, targetDayKey)) {
    root.$emit('msg', 'error', 'Нельзя вернуть запись на дату вне периода госпитализации');
    return;
  }
  const stripPlanIn = record.plan_date_in || record.date_in || targetDayKey;
  const stripPlanOut = record.plan_date_out || record.date_out || defaultPlanDateOut(targetDayKey);
  if (!assertCanAcceptPatientInCell(targetBedPk, stripPlanIn, record.direction_pk)) {
    return;
  }
  if (!assertNoBedPeriodOverlap(targetBedPk, stripPlanIn, stripPlanOut, null)) {
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
    plan_date_in: stripPlanIn,
    plan_date_out: stripPlanOut,
    accompanyng_child_type: record.accompanyng_child_type || '',
    is_need_sick: Boolean(record.is_need_sick),
    is_extract: Boolean(record.is_extract),
    comment_date: targetDayKey,
    comment: commentForRecordDay(record, targetDayKey),
  });
  if (result?.ok) {
    if (departmentPk.value && record.direction_pk) {
      const delRes = await api('chambers/delete-patient-without-bed', {
        department_pk: departmentPk.value,
        patient_obj: { direction_pk: record.direction_pk },
      });
      if (!delRes?.ok) {
        await store.dispatch(actions.DEC_LOADING);
        root.$emit('msg', 'error', delRes?.message || 'Не удалось удалить черновик на сервере');
        return;
      }
    }
    root.$emit('msg', 'ok', 'Запись возвращена на койку');
    await loadCalendar();
    await loadUnallocatedPatients();
    await reloadStripFromServer();
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось вернуть запись на койку');
  }
  await store.dispatch(actions.DEC_LOADING);
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
  const panelPlanIn = dayKey;
  const panelPlanOut = defaultPlanDateOut(dayKey);
  const occupying = bedDayOccupyingRecords(bedPk, dayKey);
  const existingForDirection = occupying.find((r) => r.direction_pk === directionPk) || null;

  if (!existingForDirection && !assertCanAcceptPatientInCell(bedPk, dayKey)) {
    return;
  }
  if (!existingForDirection && !assertNoBedPeriodOverlap(bedPk, panelPlanIn, panelPlanOut, null)) {
    return;
  }

  await store.dispatch(actions.INC_LOADING);
  let result;
  if (existingForDirection?.pk) {
    result = await api('chambers/update-hospitalization-record', {
      record_pk: existingForDirection.pk,
      doctor_id: existingForDirection.doctor_pk ?? null,
      patient_fio_text: existingForDirection.patient_fio || '',
      patient_sex: existingForDirection.patient_sex || 'м',
      birthday: existingForDirection.birthday || null,
      patient_age_text: existingForDirection.patient_age_text || '',
      plan_date_in: existingForDirection.plan_date_in || existingForDirection.date_in || null,
      plan_date_out: existingForDirection.plan_date_out || existingForDirection.date_out || null,
      accompanyng_child_type: existingForDirection.accompanyng_child_type || '',
      is_need_sick: Boolean(existingForDirection.is_need_sick),
      direction_id: directionPk,
      comment_date: dayKey,
      comment: commentForRecordDay(existingForDirection, dayKey),
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
      plan_date_in: panelPlanIn,
      plan_date_out: panelPlanOut,
      auto_default_period: true,
      fill_patient_from_direction: true,
      accompanyng_child_type: '',
      comment_date: dayKey,
      comment: '',
    });
  }
  await store.dispatch(actions.DEC_LOADING);
  if (result?.ok) {
    root.$emit('msg', 'ok', existingForDirection?.pk ? 'Направление привязано' : 'Госпитализация создана');
    removeUnallocatedPatientByDirection(directionPk);
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
  const stripRecordPk = e.dataTransfer?.getData('application/x-l2-strip-record-pk');
  if (stripRecordPk) {
    await onStripToBedDrop(bedPk, dayKey, stripRecordPk);
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
    isNeedSick: Boolean(record?.is_need_sick),
    moveToDayDraft: false,
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

const openEditModalForRecord = (bedPk: number, dayKey: string, record: CalendarRecord) => {
  if (suppressCellClick.value) {
    return;
  }
  editingStripRowId.value = null;
  fillEditModalFromRecord(record, bedPk, dayKey);
  isEditModalOpen.value = true;
};

const openStripRecordModal = (record: CalendarRecord) => {
  if (suppressCellClick.value) {
    return;
  }
  const dayKey = record.plan_date_in || record.date_in || stripDefaultDayKey.value;
  editingStripRowId.value = STRIP_BOARD_ID;
  editingStripRecordPk.value = record.pk;
  fillEditModalFromRecord(record, 0, dayKey);
  editingRecordPk.value = null;
  isEditModalOpen.value = true;
};

const setEditingDoctor = (value: number | null | undefined) => {
  const pk = value != null && Number.isFinite(Number(value)) ? Number(value) : null;
  editingForm.value = {
    ...editingForm.value,
    doctorPk: pk,
    doctorFio: pk != null ? doctorFioByPk(pk) : '',
  };
};

const setAccompanyngChildType = (value: string | null | undefined) => {
  editingForm.value = {
    ...editingForm.value,
    accompanyngChildType: value ?? null,
  };
};

const saveEditingCell = async () => {
  if (!departmentPk.value) {
    return;
  }
  const isStripEdit = Boolean(editingStripRowId.value);
  if (!isStripEdit && !editingBedPk.value) {
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
    const rec = findStripRecordByPk(editingStripRecordPk.value ?? -1);
    if (!rec) {
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
    rec.is_need_sick = Boolean(editingForm.value.isNeedSick);
    rec.direction_pk = directionIdPayload;
    rec.date_comments = { ...(rec.date_comments || {}), [editingDayKey.value]: commentPayload };
    if (!rec.direction_pk) {
      root.$emit('msg', 'error', 'Укажите номер направления для черновика');
      return;
    }
    const stripSaveRes = await saveStripPatientToServer(rec);
    if (!stripSaveRes?.ok) {
      root.$emit('msg', 'error', stripSaveRes?.message || 'Не удалось сохранить черновик на сервере');
      return;
    }
    if (rec.direction_pk) {
      removeUnallocatedPatientByDirection(rec.direction_pk);
    }
    await reloadStripFromServer();
    await loadUnallocatedPatients();
    root.$emit('msg', 'ok', 'Данные черновика сохранены');
    closeEditModal();
    return;
  }
  if (editingForm.value.moveToDayDraft && editingRecordPk.value) {
    if (!directionIdPayload) {
      root.$emit('msg', 'error', 'Для переноса в Дневные укажите номер направления');
      return;
    }
    const existingRec = records.value.find((r) => r.pk === editingRecordPk.value);
    if (!existingRec) {
      root.$emit('msg', 'error', 'Запись госпитализации не найдена');
      return;
    }
    const planIn = editingForm.value.planDateIn
      || existingRec.plan_date_in
      || existingRec.date_in
      || editingDayKey.value;
    const planOut = editingForm.value.planDateOut
      || existingRec.plan_date_out
      || existingRec.date_out
      || defaultPlanDateOut(planIn);
    const stripRec: CalendarRecord = {
      ...existingRec,
      bed_pk: 0,
      doctor_pk: editingForm.value.doctorPk,
      doctor_fio: editingForm.value.doctorFio,
      patient_fio: editingForm.value.patientFioText,
      patient_sex: editingForm.value.patientSex || 'м',
      birthday: editingForm.value.birthday || null,
      patient_age_text: editingForm.value.patientAgeText,
      direction_pk: directionIdPayload,
      plan_date_in: planIn,
      plan_date_out: planOut,
      date_in: planIn,
      date_out: editingForm.value.planDateOut || existingRec.date_out || null,
      accompanyng_child_type: editingForm.value.accompanyngChildType || '',
      is_day_hosp: true,
      is_need_sick: Boolean(editingForm.value.isNeedSick),
      date_comments: { ...(existingRec.date_comments || {}), [editingDayKey.value]: commentPayload },
    };

    await store.dispatch(actions.INC_LOADING);
    const clearRes = await api('chambers/clear-patient-from-bed', {
      record_pk: editingRecordPk.value,
    });
    if (!clearRes?.ok) {
      await store.dispatch(actions.DEC_LOADING);
      root.$emit('msg', 'error', clearRes?.message || 'Не удалось освободить койку');
      return;
    }
    const stripSaveRes = await saveStripPatientToServer(stripRec);
    if (!stripSaveRes?.ok) {
      await store.dispatch(actions.DEC_LOADING);
      root.$emit('msg', 'error', stripSaveRes?.message || 'Не удалось сохранить черновик на сервере');
      return;
    }
    await loadCalendar();
    await reloadStripFromServer();
    await loadUnallocatedPatients();
    await store.dispatch(actions.DEC_LOADING);
    root.$emit('msg', 'ok', 'Пациент перенесён в Дневные (черновики)');
    closeEditModal();
    return;
  }
  if (!editingRecordPk.value && !assertCanAcceptPatientInCell(
    editingBedPk.value,
    editingForm.value.planDateIn || editingDayKey.value,
    directionIdPayload,
  )) {
    return;
  }
  if (!assertNoBedPeriodOverlap(
    editingBedPk.value,
    editingForm.value.planDateIn,
    editingForm.value.planDateOut,
    editingRecordPk.value,
  )) {
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
      is_need_sick: Boolean(editingForm.value.isNeedSick),
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
      is_need_sick: Boolean(editingForm.value.isNeedSick),
      comment_date: editingDayKey.value,
      comment: commentPayload,
      comment_replicate_following: editingForm.value.commentReplicateFollowing,
    });
  }
  await store.dispatch(actions.DEC_LOADING);
  if (result?.ok) {
    root.$emit('msg', 'ok', 'Данные сохранены');
    closeEditModal();
    if (directionIdPayload) {
      removeUnallocatedPatientByDirection(directionIdPayload);
    }
    await loadCalendar();
    await loadUnallocatedPatients();
  } else {
    root.$emit('msg', 'error', result?.message || 'Не удалось сохранить запись');
  }
};

const clearStripFromModal = async () => {
  if (!editingStripRowId.value || editingStripRecordPk.value == null) {
    return;
  }
  const rec = findStripRecordByPk(editingStripRecordPk.value);
  await store.dispatch(actions.INC_LOADING);
  if (departmentPk.value && rec?.direction_pk) {
    const res = await api('chambers/delete-patient-without-bed', {
      department_pk: departmentPk.value,
      patient_obj: { direction_pk: rec.direction_pk },
    });
    if (!res?.ok) {
      await store.dispatch(actions.DEC_LOADING);
      root.$emit('msg', 'error', res?.message || 'Не удалось удалить черновик на сервере');
      return;
    }
  }
  await reloadStripFromServer();
  await loadUnallocatedPatients();
  await store.dispatch(actions.DEC_LOADING);
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

watch(customPeriodStart, syncCustomPeriodEndConstraints);
watch(customPeriodEnd, syncCustomPeriodEndConstraints);
watch(canMoveToDayDraft, (canMove) => {
  if (!canMove && editingForm.value.moveToDayDraft) {
    editingForm.value.moveToDayDraft = false;
  }
});

watch(isCustomPeriodMode, async (enabled, prev) => {
  if (enabled && !canUseCustomPeriod.value) {
    isCustomPeriodMode.value = false;
    return;
  }
  if (enabled) {
    const { start, end } = computeStandardPeriodRange();
    const startKey = start.format('YYYY-MM-DD');
    const endKey = end.format('YYYY-MM-DD');
    customPeriodStart.value = startKey;
    customPeriodEnd.value = endKey;
    appliedCustomPeriodStart.value = startKey;
    appliedCustomPeriodEnd.value = endKey;
    return;
  }
  if (prev) {
    appliedCustomPeriodStart.value = '';
    appliedCustomPeriodEnd.value = '';
    customPeriodStart.value = '';
    customPeriodEnd.value = '';
    await refreshBoard();
  }
});

watch(canUseCustomPeriod, (allowed) => {
  if (!allowed && isCustomPeriodMode.value) {
    isCustomPeriodMode.value = false;
  }
});

watch([viewMode, anchorDate], async () => {
  if (isCustomPeriodActive.value) {
    scheduleAsideScrollBoundsUpdate();
    return;
  }
  await loadCalendar();
  await loadUnallocatedPatients();
  await reloadStripFromServer();
  scheduleAsideScrollBoundsUpdate();
});

watch(departmentPk, async () => {
  await loadDoctors();
  doctorPk.value = -1;
  resetAsideScroll();
  scheduleAsideScrollBoundsUpdate();
  if (isCustomPeriodActive.value) {
    await reloadStripFromServer();
    return;
  }
  await Promise.all([
    loadCalendar(),
    loadUnallocatedPatients(),
    reloadStripFromServer(),
  ]);
});

watch(
  [
    unallocatedPatientsFiltered,
    dischargedPatientsInPeriod,
    unallocatedSearch,
    stripRecordsInPeriod,
    recordsForMainGrid,
    chamberRowsForDisplay,
  ],
  () => {
    scheduleAsideScrollBoundsUpdate();
  },
);

watch(hasBoardPatientFilters, async (active) => {
  if (!active) {
    return;
  }
  await nextTick();
  boardBodyRef.value?.scrollTo({ top: 0, behavior: 'smooth' });
});

onMounted(async () => {
  window.addEventListener('mouseup', stopAsideScrollHold);
  window.addEventListener('touchend', stopAsideScrollHold);
  window.addEventListener('touchcancel', stopAsideScrollHold);
  await Promise.all([loadDepartments(), loadAccompanyingChildOptions()]);
  await nextTick();
  if (typeof ResizeObserver !== 'undefined') {
    asideScrollResizeObserver = new ResizeObserver(() => {
      updateAsideScrollBounds();
    });
    if (calendarWrapRef.value) {
      asideScrollResizeObserver.observe(calendarWrapRef.value);
    }
    if (boardAsideViewport.value) {
      asideScrollResizeObserver.observe(boardAsideViewport.value);
    }
    if (boardAsideContent.value) {
      asideScrollResizeObserver.observe(boardAsideContent.value);
    }
    if (boardPatientsAside.value) {
      asideScrollResizeObserver.observe(boardPatientsAside.value);
    }
  }
  scheduleAsideScrollBoundsUpdate();
});

onBeforeUnmount(() => {
  window.removeEventListener('mouseup', stopAsideScrollHold);
  window.removeEventListener('touchend', stopAsideScrollHold);
  window.removeEventListener('touchcancel', stopAsideScrollHold);
  stopAsideScrollHold();
  if (asideScrollResizeObserver != null) {
    asideScrollResizeObserver.disconnect();
    asideScrollResizeObserver = null;
  }
});
</script>

<style scoped lang="scss">
.board-page {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  padding: 10px 8px;
}

.board-body {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

.board-patients-aside {
  flex: 0 0 304px;
  width: 304px;
  max-width: 304px;
  border-left: 1px solid #ddd;
  padding: 0 0 8px 8px;
  margin-left: 6px;
  display: flex;
  flex-direction: column;
  gap: 0;
  background: hsla(30, 3%, 94%, 1);
  align-self: flex-start;
  overflow: visible;
  box-sizing: border-box;
}

.board-aside-scroll-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.board-aside-scroll-controls--toolbar {
  gap: 3px;
}

.board-aside-scroll-btn--toolbar {
  min-width: 28px;
  width: 28px;
  height: 28px;
  padding: 0;
  line-height: 1;
  font-size: 15px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.board-aside-scroll-btn {
  min-width: 24px;
  padding: 1px 4px;
  line-height: 1.3;
  font-weight: 600;
}

.board-patients-heading-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 8px 0 6px;
  flex-shrink: 0;
}

.board-patients-heading {
  text-align: left;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.board-aside-viewport {
  flex: 0 0 auto;
  overflow: visible;
  box-sizing: border-box;
}

.board-aside-content {
  will-change: transform;
}

.board-aside-section {
  display: flex;
  flex-direction: column;
  flex: 0 0 auto;
  min-height: 0;
  overflow: visible;
}

.board-aside-section--discharged {
  border-top: 1px solid #ddd;
}

.board-aside-section-body {
  flex: 0 0 auto;
  overflow: visible;
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

.board-patient-row--discharged {
  cursor: default;
}

.board-patient-row--discharged:active {
  cursor: default;
}

.board-patient-row--discharged .board-patient-link {
  color: #333;
  text-decoration: none;
}

.board-patient-row--discharged .board-patient-link:hover,
.board-patient-row--discharged .board-patient-link:focus,
.board-patient-row--discharged .board-patient-link:visited {
  color: #333;
  text-decoration: none;
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

.board-discharged-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin: 4px 0;
  padding: 5px 8px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  font-size: 13px;
  line-height: 1.3;
}

.board-discharged-name {
  flex: 1;
  min-width: 0;
  word-break: break-word;
}

.board-discharged-date {
  flex-shrink: 0;
  font-size: 12px;
  color: #666;
}

.board-patient--women {
  color: #ff73ea;
}

.board-patient--man {
  color: #00bfff;
}

.toolbar {
  position: sticky;
  top: 0;
  z-index: 30;
  flex-shrink: 0;
  margin-bottom: 8px;
  background: #fff;
}

.toolbar.panel-flt > .panel-body {
  padding-left: 0;
  padding-right: 0;
}

.toolbar-layout {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  min-width: 0;
}

.toolbar-calendar-col {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.toolbar-aside-panel {
  flex: 0 0 304px;
  width: 304px;
  max-width: 304px;
  margin-left: 6px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 4px;
  padding: 0 2px 0 8px;
  box-sizing: border-box;
}

.toolbar-aside-search-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.toolbar-aside-search-row .board-aside-scroll-controls--toolbar {
  flex-shrink: 0;
}

.toolbar-quick-filters {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: flex-start;
  gap: 6px 8px;
  padding: 0 2px;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.toolbar-quick-filter {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 3px;
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  color: #444;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.toolbar-quick-filter input[type="checkbox"] {
  margin: 0;
  position: static;
}

.toolbar-quick-filter-counts {
  flex: 0 1 auto;
  min-width: 0;
  font-size: 11px;
  font-weight: 600;
  color: #337ab7;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toolbar-aside-search-wrap {
  flex: 1 1 auto;
  min-width: 0;
  position: relative;
}

.toolbar-aside-search {
  width: 100%;
  margin: 0;
  height: 34px;
  padding: 6px 28px 6px 10px;
  font-size: 14px;
  line-height: 20px;
  box-sizing: border-box;
}

.toolbar-aside-search-clear {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  color: #888;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
}

.toolbar-aside-search-clear:hover,
.toolbar-aside-search-clear:focus {
  color: #333;
  outline: none;
}

.toolbar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-department {
  flex: 0 1 auto;
  width: 427px;
  max-width: 43%;
  min-width: 267px;
}

.toolbar-department-treeselect {
  width: 100%;
}

.toolbar-department ::v-deep .vue-treeselect {
  width: 100%;
  min-width: 0;
}

.toolbar-department ::v-deep .vue-treeselect__control {
  overflow: hidden;
  border-radius: 4px !important;
}

.toolbar-department ::v-deep .vue-treeselect__single-value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.toolbar-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
  margin-left: auto;
}

.toolbar-controls--nav {
  flex: 1 1 auto;
  min-width: 0;
}

.mode-switch {
  display: flex;
  align-items: center;
  gap: 4px;
}

.mode-switch .active {
  background: #049372;
  color: #fff;
}

.mode-switch--period-frozen .btn:disabled,
.btn-group--period-frozen .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.toolbar-period-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  user-select: none;
}

.toolbar-period-toggle input {
  margin: 0;
}

.toolbar-custom-period {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
  flex-shrink: 0;
  white-space: nowrap;
}

.toolbar-custom-period-sep {
  flex-shrink: 0;
  font-weight: 600;
  font-size: 14px;
  color: #555;
  line-height: 1;
  padding: 0 1px;
}

.toolbar-custom-period-input {
  width: 108px;
  min-width: 108px;
  height: 34px;
  padding: 6px 4px;
  font-size: 12px;
  line-height: 20px;
  box-sizing: border-box;
}

.board-discharged-heading-row {
  margin-top: 4px;
}

.board-discharged-heading {
  margin: 0;
}

.board-discharged-heading-link {
  color: #0d47a1;
  font-size: 14px;
  font-weight: 600;
  text-decoration: underline;
  cursor: pointer;
}

.board-discharged-heading-link:hover,
.board-discharged-heading-link:focus {
  color: #1565c0;
  text-decoration: underline;
}

.calendar-wrap {
  display: flex;
  flex-direction: column;
  width: 100%;
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  container-type: inline-size;
  container-name: calendar-wrap;
}

.calendar-tables-stack {
  display: flex;
  flex-direction: column;
  flex: 0 0 auto;
}

.calendar-main-scroll {
  flex: 0 0 auto;
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: visible;
}

.calendar-main-scroll--search-compact {
  flex: 0 1 auto;
  max-height: min(55vh, 520px);
  overflow-y: auto;
}

.calendar-strip-block {
  flex: 0 0 auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  margin-top: 0;
  padding-top: 4px;
  padding-bottom: 4px;
}

.calendar-table {
  table-layout: fixed;
  width: 100%;
}

/* Месяц: столбец даты в 2 раза уже, чем столбец даты недели */
.calendar-table--month {
  width: auto;
  min-width: 100%;
}

.calendar-table--month .calendar-col-day {
  width: calc((100cqi - 88px - 64px) / 7 / 2);
  min-width: 56px;
}

.calendar-table--month .day-col,
.calendar-table--month .day-cell {
  width: calc((100cqi - 88px - 64px) / 7 / 2);
  min-width: 56px;
  max-width: none;
}

.calendar-table--month .day-cell {
  overflow: hidden;
}

.doctor-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex-shrink: 0;
}

.doctor-badges--toolbar {
  margin: 0;
  padding: 0 0 2px;
  width: 100%;
  box-sizing: border-box;
}

.doctor-badge-btn {
  border: none;
  border-radius: 4px;
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
  width: 88px;
}

.calendar-col-bed {
  width: 64px;
}

.calendar-col-day {
  width: auto;
  min-width: 108px;
}

.chamber-col {
  width: 88px;
  min-width: 88px;
  max-width: 88px;
}

.bed-col {
  width: 64px;
  min-width: 64px;
  max-width: 64px;
}

.day-col {
  width: auto;
  min-width: 108px;
  text-align: center;
}

.day-col--today {
  background: #f2f2f2;
}

.day-col--header {
  cursor: default;
}

.day-col--hover,
.day-cell--col-hover {
  background: rgba(91, 143, 175, 0.12);
}

.day-col--today.day-col--hover {
  background: rgba(91, 143, 175, 0.16);
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
  left: 88px;
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
  padding: 0;
  cursor: pointer;
  width: auto;
  min-width: 108px;
  overflow: hidden;
}

.day-cell--drop-hover {
  box-shadow: inset 0 0 0 2px #049372;
  background: rgba(4, 147, 114, 0.12);
}

.record {
  background: #fff;
  border: none;
  padding: 0;
  margin: 0;
  color: inherit;
  font-size: 12px;
  line-height: 1.25;
  text-align: left;
  box-sizing: border-box;
}

.record:not(:last-child) {
  margin-bottom: 2px;
}

.record--extract {
  background: #e6e6e6;
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
  vertical-align: baseline;
  min-width: 0;
}

.record-patient-surname {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
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
  margin-top: 0;
  min-width: 0;
}

.record-doctor-line-inner {
  display: block;
  flex: 1;
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

.record-sick-badge {
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  user-select: none;
  flex-shrink: 0;
  margin-left: auto;
  color: #800020;
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
  padding: 16px;
  overflow-y: auto;
}

.edit-modal {
  width: 560px;
  max-width: calc(100vw - 32px);
  max-height: calc(100vh - 32px);
  margin: auto;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.edit-modal .panel-heading {
  flex-shrink: 0;
}

.edit-modal .panel-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.edit-modal .panel-footer {
  flex-shrink: 0;
}

.edit-modal-treeselect {
  position: relative;
  z-index: 2;
}

.edit-modal-comment-replicate {
  margin-top: 8px;
}

.edit-modal-comment-replicate .help-block {
  margin-bottom: 0;
}

.modal-gender-sick-row .modal-sick-col {
  padding-top: 5px;
}

.modal-gender-sick-row .modal-sick-checkbox-list {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.modal-gender-sick-row .modal-sick-checkbox {
  margin: 0;
  padding: 0;
  min-height: 0;
}

.modal-gender-sick-row .modal-sick-checkbox label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding-left: 0;
  font-weight: normal;
  line-height: 1;
}

.modal-gender-sick-row .modal-sick-checkbox input[type="checkbox"] {
  margin: 0;
  position: static;
}

.strip-board-hint {
  margin: 0 0 4px;
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  line-height: 1.2;
}

.strip-cards-board {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 6px;
  align-content: start;
  width: 100%;
  padding: 4px 10px 8px;
  box-sizing: border-box;
}

/* Дополнительная строка под DnD, когда ряд заполнен (6 карточек) или зона пуста */
.strip-cards-board--extra-drop-row::after {
  content: '';
  display: block;
  grid-column: 1 / -1;
  min-height: 52px;
  pointer-events: none;
}

.strip-cards-board--drop-hover {
  outline: 2px dashed #049372;
  outline-offset: 2px;
  background: rgba(4, 147, 114, 0.06);
}

.strip-cards-empty {
  grid-column: 1 / -1;
  margin: 0;
}

.strip-card {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-height: 0;
  padding: 3px 8px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  cursor: pointer;
}

.strip-card--drop-hover {
  box-shadow: inset 0 0 0 2px #049372;
  background: rgba(4, 147, 114, 0.08);
}

.strip-card--forbidden-edit {
  background: #e6e6e6;
}

.strip-card-doctor-aside {
  display: inline-flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.strip-card-period {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  line-height: 1.1;
  white-space: nowrap;
}

.strip-card .record-line {
  font-size: 12px;
  line-height: 1.2;
}

.strip-card .record-line--doctor {
  min-height: 0;
  margin: 0;
  padding: 0;
}

@media (max-width: 1400px) {
  .strip-cards-board {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 992px) {
  .strip-cards-board {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
