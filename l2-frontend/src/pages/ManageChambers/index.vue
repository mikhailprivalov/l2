<template>
  <div>
    <div
      ref="root"
      class="construct-root"
    >
      <div class="construct-sidebar">
        <Filters
          :filters="filters"
          :departments="departments"
        />
        <div
          class="sidebar-content"
        >
          <h5
            style="text-align: center"
          >
            Пациенты
          </h5>
          <draggable
            v-model="unallocatedPatients"
            :options="{group:{ name: 'Patients', put: 'Patients', pull: 'Patients'}, sort: false, ForceFallback: true}"
            class="draggable-element"
            chosen-class="dragClass"
            animation="500"
          >
            <div
              v-for="patient in unallocatedPatients"
              :key="patient.pk"
              class="content-research"
            >
              {{ patient.fio }}
              <i
                class="fa-solid fa-child-reaching"
                :class="{ 'women': changeColorWomen(patient), 'man': changeColorMan(patient) }"
                style="font-size: 20px"
              />
              {{ patient.age }}л.
            </div>
          </draggable>
        </div>
      </div>
    </div>
    <div class="construct-bottom-root">
      <div class="construct-bottom-bar">
        <div class="bottom-bar-content-home">
          <h5 style="text-align: center">
            Ожидающие
          </h5>
          <draggable
            v-model="withOutBeds"
            :options="{group:{
                         name: 'Patients',
                         pull: 'Patients',
                         put: 'Patients'},
                       sort: false,
                       ForceFallback: true}"
            class="draggable-element-home"
            chosen-class="dragClass"
            animation="500"
            @change="PatientWaitBed"
          >
            <div
              v-for="patient in withOutBeds"
              :key="patient.pk"
              class="content-research-waiting"
            >
              {{ patient.short_fio }}
              <i
                class="fa-solid fa-child-reaching"
                :class="{ 'women': changeColorWomen(patient), 'man': changeColorMan(patient) }"
                style="font-size: 20px"
              />
              {{ patient.age }}л.
            </div>
          </draggable>
        </div>
      </div>
    </div>
    <div class="scroll-div">
      <table class="table table-fixed table-bordered table-responsive table-condensed chamber-table">
        <colgroup>
          <col width="80">
          <col width="855">
        </colgroup>
        <thead class="sticky">
          <tr>
            <th
              class="header-alignment"
            >
              Номер палаты
            </th>
            <th>
              Управление койками
              (Кол.коек: {{ bedInformationCounter.bed }},
              Занятых: {{ bedInformationCounter.occupied }},
              М: {{ bedInformationCounter.man }},
              Ж: {{ bedInformationCounter.women }})
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="chamber in chambers"
            :key="chamber.pk"
            style="max-height: 61px; height: 61px"
          >
            <td
              class="string-alignment"
            >
              {{ chamber.label }}
            </td>
            <td class="margins">
              <div
                v-for="bed in chamber.beds"
                :key="bed.pk"
                class="element"
                :class="{ 'padding-element': bed.patient.length < 1}"
              >
                <draggable
                  v-model="bed.doctor"
                  :options="{group:{
                               name: 'doctor',
                               put: conditionsDragDoc(bed),
                               pull: 'attendingDoctor'},
                             sort: false}"
                  animation="500"
                  class="drag-and-drop"
                  @change="changeDoctor($event, bed);"
                >
                  <i
                    v-if="bed.doctor.length > 0"
                    class="fa-solid fa-user-doctor"
                    :class="{ 'women': colorWomen(bed), 'man': colorMan(bed) }"
                    style="font-size: 20px"
                  />
                  <span
                    v-if="bed.doctor.length < 1"
                    style="font-size: 12px"
                  >
                    Б/В
                  </span>
                </draggable>
                <draggable
                  v-model="bed.patient"
                  :options="{
                    group:{
                      name: 'Patients',
                      put: conditionsDragBed(bed),
                      pull: 'Patients'
                    },
                    sort: false}"
                  animation="500"
                  class="drag-and-drop-patient"
                  @change="changePatientBed($event, bed)"
                  @remove="clearArrayDoctor(bed)"
                >
                  <div
                    style="display: inline-block"
                  >
                    <div
                      v-if="bed.patient.length > 0"
                      class="element-content"
                    >
                      {{ bed.patient[0].age }}л.
                    </div>
                    <i
                      class="fa fa-bed bedMin"
                      :class="{ 'women': colorWomen(bed), 'man': colorMan(bed) }"
                    />
                  </div>
                </draggable>
                <table
                  v-if="bed.patient.length > 0 || bed.doctor.length > 0"
                  class="table table-fixed table-bordered table-responsive table-condensed table-info"
                >
                  <tr>
                    <td
                      v-if="bed.patient.length > 0"
                    >
                      {{ bed.patient[0].short_fio }}
                    </td>
                  </tr>
                  <tr>
                    <td
                      v-if="bed.patient.length > 0"
                      style="border-top: 2px solid #ddd;"
                      :class="{'changeColorDoc': bed.patient[0].highlight}"
                    >
                      <div v-if="bed.doctor.length > 0 && bed.patient.length > 0">
                        {{ bed.doctor[0].short_fio }}
                      </div>
                    </td>
                  </tr>
                </table>
              </div>
            </td>
          </tr>
          <tr v-if="chambers.length === 0">
            <td colspan="2">
              Нет палат
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="construct-right">
      <div
        class="construct-sidebar"
      >
        <FiltersDoc
          :filters="filters"
          :departments="departments"
        />
        <div
          class="sidebar-content"
          style="width: 297px"
        >
          <h5
            style="text-align: center"
          >
            Врачи
          </h5>
          <draggable
            v-model="attendingDoctor"
            :options="{group:{ name: 'attendingDoctor', pull: 'clone', put: 'doctor'}, sort: false, ForceFallback: true}"
            class="draggable-element"
            chosen-class="dragClass"
            animation="500"
          >
            <div
              v-for="doctor in attendingDoctor"
              :key="doctor.pk"
              class="content-research"
              @click="highlight(doctor)"
            >
              {{ doctor.fio }} ({{ countPatientAtDoctor(doctor) }})
            </div>
          </draggable>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import draggable from 'vuedraggable';
import {
  computed,
  onMounted,
  ref,
  watch,
} from 'vue';

import * as actions from '@/store/action-types';
import api from '@/api';
import { useStore } from '@/store';

import Filters from './components/Filters.vue';
import FiltersDoc from './components/FiltersDoc.vue';

const chambers = ref([]);
const departments = ref([]);
const unallocatedPatients = ref([]);
const withOutBeds = ref([]);
const attendingDoctor = ref([]);
const filters = ref({
  department_pk: -1,
  departmentDoc_pk: -1,
});
const store = useStore();
const department = computed(() => filters.value.department_pk);
const departmentDoc = computed(() => filters.value.departmentDoc_pk);
const bedInformationCounter = computed(() => {
  let women = 0;
  let man = 0;
  let occupied = 0;
  let bed = 0;
  for (let i = 0; i < chambers.value.length; i++) {
    for (let j = 0; j < chambers.value[i].beds.length; j++) {
      bed += 1;
      if (chambers.value[i].beds[j].patient.length > 0) {
        occupied += 1;
        if (chambers.value[i].beds[j].patient[0].sex === 'ж') {
          women += 1;
        }
        if (chambers.value[i].beds[j].patient[0].sex === 'м') {
          man += 1;
        }
      }
    }
  }
  return {
    women,
    man,
    occupied,
    bed,
  };
});
async function init() {
  await store.dispatch(actions.INC_LOADING);
  const { data } = await api('procedural-list/suitable-departments');
  departments.value = [{ id: -1, label: 'Отделение не выбрано' }, ...data];
  await store.dispatch(actions.DEC_LOADING);
}
async function getAttendingDoctors() {
  await store.dispatch(actions.INC_LOADING);
  const row = await api('chambers/get-attending-doctors', {
    department_pk: departmentDoc.value,
  });
  attendingDoctor.value = row.data;
  await store.dispatch(actions.DEC_LOADING);
}
async function getUnallocatedPatients() {
  await store.dispatch(actions.INC_LOADING);
  const row = await api('chambers/get-unallocated-patients', {
    department_pk: department.value,
  });
  unallocatedPatients.value = row.data;
  await store.dispatch(actions.DEC_LOADING);
}
async function getPatientWithoutBed() {
  await store.dispatch(actions.INC_LOADING);
  const row = await api('chambers/get-patients-without-bed', {
    department_pk: department.value,
  });
  withOutBeds.value = row.data;
  await store.dispatch(actions.DEC_LOADING);
}
async function loadChamberAndBed() {
  await store.dispatch(actions.INC_LOADING);
  const row = await api('chambers/get-chambers-and-beds', {
    department_pk: department.value,
  });
  chambers.value = row.data;
  await store.dispatch(actions.DEC_LOADING);
}
async function changePatientBed({ added, removed }, bed) {
  if (added) {
    await store.dispatch(actions.INC_LOADING);
    await api('chambers/entrance-patient-to-bed', {
      bed_id: bed.pk,
      direction_id: bed.patient[0].direction_pk,
    });
    await store.dispatch(actions.DEC_LOADING);
  }
  if (removed) {
    await store.dispatch(actions.INC_LOADING);
    await api('chambers/extract-patient-bed', {
      patient: removed.element,
    });
    await store.dispatch(actions.DEC_LOADING);
  }
}
async function PatientWaitBed({ added, removed }) {
  if (added) {
    await store.dispatch(actions.INC_LOADING);
    await api('chambers/save-patient-without-bed', {
      patient_obj: added.element,
      department_pk: department.value,
    });
    await store.dispatch(actions.DEC_LOADING);
  }
  if (removed) {
    await store.dispatch(actions.INC_LOADING);
    await api('chambers/delete-patient-without-bed', {
      patient_obj: removed.element,
    });
    await store.dispatch(actions.DEC_LOADING);
  }
}
async function changeDoctor({ added, removed }, bed) {
  if (added) {
    await store.dispatch(actions.INC_LOADING);
    await api('chambers/doctor-assigned-patient', {
      doctor: added.element,
      direction_id: bed.patient[0].direction_pk,
    });
    await store.dispatch(actions.DEC_LOADING);
  }
  if (removed) {
    await getAttendingDoctors();
    await store.dispatch(actions.INC_LOADING);
    await api('chambers/doctor-detached-patient', {
      doctor: removed.element,
      direction_id: bed.patient[0].direction_pk,
    });
    await store.dispatch(actions.DEC_LOADING);
  }
}
function conditionsDragDoc(bed) {
  if (bed.patient.length > 0 && bed.doctor.length < 1) {
    return 'attendingDoctor';
  }
  return false;
}
function conditionsDragBed(bed) {
  if (bed.patient < 1) {
    return 'Patients';
  }
  return false;
}
function clearArrayDoctor(bed) {
  bed.doctor.pop();
}
function changeColorWomen(patient) {
  return patient.sex === 'ж';
}
function changeColorMan(patient) {
  return patient.sex === 'м';
}
function colorWomen(bed) {
  if (bed.patient.length > 0) {
    return bed.patient[0].sex === 'ж';
  }
  return false;
}
function colorMan(bed) {
  if (bed.patient.length > 0) {
    return bed.patient[0].sex === 'м';
  }
  return false;
}
function highlight(doctor) {
  for (let i = 0; i < chambers.value.length; i++) {
    for (let j = 0; j < chambers.value[i].beds.length; j++) {
      if (chambers.value[i].beds[j].doctor.length > 0) {
        if (chambers.value[i].beds[j].doctor[0].fio === doctor.fio) {
          chambers.value[i].beds[j].patient[0].highlight = !chambers.value[i].beds[j].patient[0].highlight;
        }
      }
    }
  }
}
function countPatientAtDoctor(doctor) {
  let patient = 0;
  for (let i = 0; i < chambers.value.length; i++) {
    for (let j = 0; j < chambers.value[i].beds.length; j++) {
      if (chambers.value[i].beds[j].doctor.length > 0) {
        if (chambers.value[i].beds[j].doctor[0].fio === doctor.fio) {
          patient += 1;
        }
      }
    }
  }
  return patient;
}
watch(department, () => {
  getUnallocatedPatients();
  loadChamberAndBed();
  getPatientWithoutBed();
});
watch(departmentDoc, () => {
  getAttendingDoctors();
});
onMounted(init);
</script>

<style scoped lang="scss">
.scroll-div {
  overflow-y: auto;
  overflow-x: hidden;
  position: absolute;
  top: 35px;
  right: 0;
  bottom: 0;
  left: 300px;
  width: 935px;
  height: 500px;
}
.construct-right {
  position: absolute;
  top: 35px;
  right: 0;
  bottom: 0;
  left: 1235px;
  width: 282px;
  border-left: 1px solid #b1b1b1;
}
.construct-bottom-root {
  position: absolute;
  top: 535px;
  right: 0;
  bottom: 0;
  left: 300px;
  border-right: 1px solid #b1b1b1;
  border-left: 1px solid #b1b1b1;
  border-top: 1px solid #b1b1b1;
  display: inline-block;
  align-items: stretch;
  flex-direction: row;
  flex-wrap: nowrap;
  align-content: stretch;

  & > div {
    align-self: stretch;
  }
}
.construct-bottom-bar {
  width: 936px;
  display: flex;
  flex-direction: column;
}
.bottom-bar-content-home {
  height: calc(100vh - 564.5px);
  overflow-y: auto;
}
.construct-root {
  position: absolute;
  top: 35px;
  right: 0;
  bottom: 0;
  left: 0;
  border-right: 1px solid #b1b1b1;
  display: inline-block;
  align-items: stretch;
  flex-direction: row;
  flex-wrap: nowrap;
  align-content: stretch;

  & > div {
    align-self: stretch;
  }
}
.construct-sidebar {
  width: 300px;
  border-right: 1px solid #b1b1b1;
  display: flex;
  flex-direction: column;
}
.sidebar-content {
  height: calc(100vh - 72px);
  overflow-y: auto;
  background-color: hsla(30, 3%, 97%, 1);
}
.draggable-element {
  padding: 5px;
  margin: 10px;
  height: 600px;
}
.draggable-element-home {
  padding: 5px;
  margin: 10px;
  height: 120px;
}
.chamber-table {
  height: 500px;
}
.table-info {
  display: inline-block;
  border: none;
  background-color: transparent;
  width: 140px;
  margin-bottom: 0;
}
.table-info tr:nth-child(2n-1) {
  background-color: transparent;
}
.table-info tr:nth-child(2n) {
  background-color: transparent;
}
.chamber-table tr:nth-child(2n) {
  background-color: #F5F5F5;
}
.chamber-table tr:nth-child(2n-1) {
  background-color: #FFFAFA;
}
.margins {
  margin-bottom: 10px;
  padding: 10px;
}
.drag-and-drop {
  display: inline-block;
  overflow: hidden;
  background-color: #fff;
  margin-left: 20px;
  margin-bottom: 10px;
  text-align: center;
  padding: 5px;
  height: 30px;
  width: 30px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

  &.rhide {
  background-image: linear-gradient(#6c7a89, #56616c);
  color: #fff;
  }

  &:hover {
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
  z-index: 1;
  transform: scale(1.008);
  }
}
.drag-and-drop-patient {
  display: inline-block;
  overflow: hidden;
  background-color: #fff;
  margin-left: 5px;
  margin-bottom: 10px;
  text-align: right;
  padding: 5px;
  height: 30px;
  width: 68px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

  &.rhide {
  background-image: linear-gradient(#6c7a89, #56616c);
  color: #fff;
  }

  &:hover {
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
  z-index: 1;
  transform: scale(1.008);
  }
}
.bedMin {
  font-size: 20px;
  overflow: hidden;
}
.women {
  color: #ffb9ea;
}
.man {
  color: #00bfff;
}
.currentDoctor {
  color:  #00bfff;
}
.content-research-waiting{
  margin-top: 10px;
  max-width: 250px;
  display: inline-block;
  margin-left: 10px;
  margin-bottom: 10px;
  background-color: #fff;
  padding: 5px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

  &.rhide {
  background-image: linear-gradient(#6c7a89, #56616c);
  color: #fff;
  }

  &:hover {
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
  z-index: 1;
  transform: scale(1.008);
  }
}
.content-research {
  margin-top: 10px;
  margin-bottom: 10px;
  background-color: #fff;
  padding: 5px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

  &.rhide {
  background-image: linear-gradient(#6c7a89, #56616c);
  color: #fff;
  }

  &:hover {
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
  z-index: 1;
  transform: scale(1.008);
  }
}
.element {
  display: inline-block;
}
.padding-element {
  padding-right: 140px;
}
.element-content {
  display: inline-block;
  margin-right: 1px;
  margin-bottom: 10px;
}
.string-alignment {
  font-weight: bold;
  text-align: center;
  vertical-align: middle;
}
.header-alignment {
  text-align: center;
  vertical-align: middle;
}
.dragClass {
  opacity: 0;
}
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  box-shadow: inset 0 0 6px rgba(0,0,0,0.3);
}
::-webkit-scrollbar-thumb {
  box-shadow: inset 0 0 6px rgba(0,0,0,0.3);
}
.sticky {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: white;
}
.changeColorDoc {
  background-color: #BCD2DD;
}
</style>
