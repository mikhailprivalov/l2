<template>
  <div class="three-panel">
    <div class="panel-left">
      <Filters
        :departments="departments"
        :no-border="true"
        @input="setDepartPatientId"
      />
      <h5
        class="heading top-border"
      >
        Пациенты
      </h5>
      <div
        class="panel-content"
      >
        <draggable
          v-model="unallocatedPatients"
          :group="{ name: 'Patients', put: ['PatientWithoutBeds', 'Beds'], pull: ['PatientWithoutBeds', 'Beds']}"
          class="draggable-block"
          animation="500"
          chosen-class="chosen-unallocated-patient"
          ghost-class="ghost-unallocated-patient"
        >
          <div
            v-for="patient in unallocatedPatients"
            :key="patient.direction_pk"
            class="draggable-item"
          >
            {{ patient.fio }}
            <i
              class="fa-solid fa-child-reaching icon-patient"
              :class="{ 'women': changeColorWomen(patient), 'man': changeColorMan(patient) }"
            />
            {{ patient.age }}л.
          </div>
        </draggable>
      </div>
    </div>
    <div class="panel-center">
      <div class="room-beds">
        <table class="table-beds table-bordered table-responsive table-condensed chamber-table">
          <colgroup>
            <col class="width80">
            <col>
          </colgroup>
          <thead class="sticky">
            <tr class="height36">
              <th
                class="header-alignment"
              >
                Палата
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
            >
              <td
                class="room-number"
              >
                {{ chamber.label }}
              </td>
              <td>
                <div class="beds">
                  <div
                    v-for="bed in chamber.beds"
                    :key="bed.pk"
                    class="beds-item"
                  >
                    <draggable
                      v-model="bed.doctor"
                      :group="{
                        name: 'doctor',
                        put: checkConditionsPutDoc(bed.patient, bed.doctor),
                        pull: checkConditionsPullDoc(bed.doctor)
                      }"
                      animation="500"
                      class="draggable-doctor"
                      chosen-class="chosen-doctor"
                      ghost-class="ghost-doctor"
                      @change="changeDoctor($event, bed);"
                    >
                      <div class="flex">
                        <i
                          v-if="bed.doctor.length > 0"
                          class="fa-solid fa-user-doctor icon-doctor"
                          :class="{ 'women': colorWomen(bed), 'man': colorMan(bed) }"
                        />
                        <div
                          v-if="bed.doctor.length < 1"
                          class="without-doctor"
                        >
                          Б/В
                        </div>
                      </div>
                    </draggable>
                    <draggable
                      v-model="bed.patient"
                      :group="{
                        name: 'Beds',
                        put: checkConditionsPutBed(bed.patient),
                        pull: checkConditionsPullBed(bed.patient)
                      }"
                      animation="500"
                      class="draggable-beds"
                      chosen-class="chosen-beds"
                      ghost-class="ghost-beds"
                      @change="changePatientBed($event, bed)"
                      @remove="clearArrayDoctor(bed)"
                    >
                      <div class="patient-row">
                        <div
                          v-if="bed.patient.length > 0"
                          class="age"
                        >
                          {{ bed.patient[0].age }}л.
                        </div>
                        <i
                          class="fa fa-bed icon-beds"
                          :class="{ 'women': colorWomen(bed), 'man': colorMan(bed) }"
                        />
                      </div>
                    </draggable>
                    <div
                      v-if="bed.patient.length > 0 || bed.doctor.length > 0"
                      class="info"
                    >
                      <div
                        v-if="bed.patient.length > 0"
                        class="text-size"
                      >
                        {{ bed.patient[0].short_fio }}
                      </div>
                      <hr
                        v-if="bed.doctor.length > 0"
                        class="line"
                      >
                      <div
                        v-if="bed.doctor.length > 0"
                        class="text-size"
                        :class="{'change-color-doc': bed.doctor[0].highlight}"
                      >
                        {{ bed.doctor[0].short_fio }}
                      </div>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
            <tr v-if="chambers.length === 0">
              <td
                class="no-rooms"
                colspan="2"
              >
                Нет палат
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="waiting">
        <h5
          class="heading"
        >
          Ожидающие
        </h5>
        <div class="waiting-content">
          <draggable
            v-model="withOutBeds"
            :group="{
              name: 'PatientWithoutBeds',
              pull: ['PatientWithoutBeds', 'Patients', 'Beds'],
              put: ['PatientWithoutBeds', 'Patients', 'Beds']
            }"
            class="draggable-block-waiting"
            chosen-class="chosen-patient-without-bed"
            ghost-class="ghost-patient-without-bed"
            animation="500"
            @change="PatientWaitBed"
          >
            <div
              v-for="patient in withOutBeds"
              :key="patient.direction_pk"
              class="draggable-item waiting-item"
            >
              {{ patient.short_fio }}
              <i
                class="fa-solid fa-child-reaching icon-patient"
                :class="{ 'women': changeColorWomen(patient), 'man': changeColorMan(patient) }"
              />
              {{ patient.age }}л.
            </div>
          </draggable>
        </div>
      </div>
    </div>
    <div class="panel-right">
      <Filters
        :departments="departments"
        :no-border="true"
        @input="setDepartDocId"
      />
      <h5 class="heading top-border">
        Врачи
      </h5>
      <div class="panel-content">
        <draggable
          v-model="attendingDoctor"
          :group="{ name: 'attendingDoctor', pull: 'clone', put: 'doctor'}"
          class="draggable-block"
          chosen-class="chosen-attending-doctor"
          ghost-class="ghost-attending-doctor"
          animation="500"
        >
          <div
            v-for="doctor in attendingDoctor"
            :key="doctor.pk"
            class="draggable-item"
            @click="highlight(doctor)"
          >
            {{ doctor.fio }} ({{ countPatientAtDoctor(doctor) }})
          </div>
        </draggable>
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

interface patientData {
  age: number
  direction_pk: number
  fio: string
  sex: string
  short_fio: string
}
interface doctorData {
  fio: string
  highlight: boolean
  pk: number
  short_fio: string
}
interface bedData {
  bed_number: number
  doctor: doctorData[]
  patient: patientData[]
  pk: number
}
interface chamberData {
  beds: bedData[]
  label: string
  pk: number
}
const chambers = ref<chamberData[]>([]);
const departments = ref([]);
const unallocatedPatients = ref<patientData[]>([]);
const withOutBeds = ref<patientData[]>([]);
const attendingDoctor = ref<doctorData[]>([]);
const departmentPatientPk = ref(null);
const departmentDocPk = ref(null);
const store = useStore();
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

const setDepartDocId = async (departmentPk) => {
  departmentDocPk.value = departmentPk;
};
const setDepartPatientId = async (departmentPk) => {
  departmentPatientPk.value = departmentPk;
};

const init = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { data } = await api('procedural-list/suitable-departments');
  departments.value = data;
  await store.dispatch(actions.DEC_LOADING);
};

const getAttendingDoctors = async () => {
  await store.dispatch(actions.INC_LOADING);
  const row = await api('chambers/get-attending-doctors', {
    department_pk: departmentDocPk.value,
  });
  attendingDoctor.value = row.data;
  await store.dispatch(actions.DEC_LOADING);
};

const getUnallocatedPatients = async () => {
  await store.dispatch(actions.INC_LOADING);
  const row = await api('chambers/get-unallocated-patients', {
    department_pk: departmentPatientPk.value,
  });
  unallocatedPatients.value = row.data;
  await store.dispatch(actions.DEC_LOADING);
};

const getPatientWithoutBed = async () => {
  await store.dispatch(actions.INC_LOADING);
  const row = await api('chambers/get-patients-without-bed', {
    department_pk: departmentPatientPk.value,
  });
  withOutBeds.value = row.data;
  await store.dispatch(actions.DEC_LOADING);
};

const loadChamberAndBed = async () => {
  await store.dispatch(actions.INC_LOADING);
  const row = await api('chambers/get-chambers-and-beds', {
    department_pk: departmentPatientPk.value,
  });
  chambers.value = row.data;
  await store.dispatch(actions.DEC_LOADING);
};

const changePatientBed = async ({ added, removed }, bed) => {
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
      patient: removed.element.direction_pk,
    });
    await store.dispatch(actions.DEC_LOADING);
  }
};

const PatientWaitBed = async ({ added, removed }) => {
  if (added) {
    await store.dispatch(actions.INC_LOADING);
    await api('chambers/save-patient-without-bed', {
      patient_obj: added.element,
      department_pk: departmentPatientPk.value,
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
};

const changeDoctor = async ({ added, removed }, bed) => {
  let doctor;
  if (added) {
    doctor = {
      doctor_pk: added.element.pk,
      direction_id: bed.patient[0].direction_pk,
      is_assign: true,
    };
  }
  if (removed) {
    await getAttendingDoctors();
    doctor = {
      doctor_pk: removed.element.pk,
      direction_id: bed.patient[0].direction_pk,
      is_assign: false,
    };
  }
  await store.dispatch(actions.INC_LOADING);
  await api('chambers/update-doctor-to-bed', { doctor });
  await store.dispatch(actions.DEC_LOADING);
};

const checkConditionsPutDoc = (patient: patientData[], doctor: doctorData[]) => {
  if (patient.length > 0 && doctor.length < 1) {
    return 'attendingDoctor';
  }
  return false;
};

const checkConditionsPullDoc = (doctor: doctorData[]) => {
  if (doctor.length > 0) {
    return 'attendingDoctor';
  }
  return false;
};

const checkConditionsPutBed = (patient: patientData[]) => {
  if (patient.length < 1) {
    return ['Beds', 'Patients', 'PatientWithoutBeds'];
  }
  return false;
};

const checkConditionsPullBed = (patient: patientData[]) => {
  if (patient.length > 0) {
    return ['Beds', 'Patients', 'PatientWithoutBeds'];
  }
  return false;
};

const clearArrayDoctor = (bed) => {
  // eslint-disable-next-line no-param-reassign
  bed.doctor = bed.doctor.filter(doctor => !bed.doctor.includes(doctor));
};

const changeColorWomen = (patient) => (patient.sex === 'ж');

const changeColorMan = (patient) => (patient.sex === 'м');

const colorWomen = (bed) => {
  if (bed.patient.length > 0) {
    return bed.patient[0].sex === 'ж';
  }
  return false;
};

const colorMan = (bed) => {
  if (bed.patient.length > 0) {
    return bed.patient[0].sex === 'м';
  }
  return false;
};

const highlight = (doctor) => {
  for (let i = 0; i < chambers.value.length; i++) {
    for (let j = 0; j < chambers.value[i].beds.length; j++) {
      if (chambers.value[i].beds[j].doctor.length > 0) {
        if (chambers.value[i].beds[j].doctor[0].fio === doctor.fio) {
          chambers.value[i].beds[j].doctor[0].highlight = !chambers.value[i].beds[j].doctor[0].highlight;
        }
      }
    }
  }
};

const countPatientAtDoctor = (doctor) => {
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
};

watch(departmentPatientPk, () => {
  getUnallocatedPatients();
  loadChamberAndBed();
  getPatientWithoutBed();
});
watch(departmentDocPk, () => {
  getAttendingDoctors();
});
onMounted(init);

</script>

<style scoped lang="scss">
.chamber-table {
  height: 100px;
}
.chamber-table tr:nth-child(2n) {
  background-color: #F5F5F5;
}
.chamber-table tr:nth-child(2n-1) {
  background-color: #FFFAFA;
}
.women {
  color: #ffb9ea;
}
.man {
  color: #00bfff;
}
.height36 {
  height: 36px;
}
.header-alignment {
  text-align: center;
  vertical-align: middle;
}
.sticky {
  position: sticky;
  top: -1px;
  z-index: 1;
  background-color: white;
}
.table-bordered > thead > tr > th {
  border-bottom-width: 0;
}
.change-color-doc {
  background-color: #BCD2DD;
}
.heading {
  text-align: center;
  margin: 0 0 5px 0;
}
.top-border {
  border-top: 1px solid #b1b1b1;
}
.flex {
  display: flex;
}

.icon {
  &-patient,
  &-doctor,
  &-beds {
    font-size: 20px;
    margin: 5px auto;
  }
  &-patient {
    margin: auto;
  }
}
.info {
  display: inline-block;
  vertical-align: top;
  width: 136px;
}
.line {
  border-top: 1px solid #ddd;
  margin-bottom: 0;
  margin-top: 0;
}
.text-size {
  font-size: 13px;
}

.three-panel {
  display: grid;
  grid-template-columns: 300px 1fr 282px;
  height: calc(100vh - 36px);
  background-color: hsla(30, 3%, 97%, 1);
}
.panel {
  &-left,
  &-center,
  &-right {
    display: flex;
    flex-direction: column;
    margin-bottom: 10px;
  }
  &-left {
    background-color: hsla(30, 3%, 97%, 1);
    border-right: 1px solid #b1b1b1;
  }
  &-right {
    background-color: hsla(30, 3%, 97%, 1);
    border-left: 1px solid #b1b1b1;
  }
  &-center {
    overflow-y: auto;
  }
}
.panel-content {
  flex: 1;
  max-height: calc(100vh - 107px);
  overflow-y: auto;
  background-color: hsla(30, 3%, 97%, 1);
}
.draggable-block {
  min-height: calc(100% - 20px);
}
.draggable {
  &-item,
  &-beds,
  &-doctor {
    margin: 5px;
    overflow: hidden;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

    &:hover {
      box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
      z-index: 1;
      transform: scale(1.008);
    }
  }
  &-item {
    margin: 10px 5px;
    padding: 5px;
  }
  &-doctor {
    height: 30px;
    width: 30px;
  }
  &-beds {
    text-align: right;
    height: 30px;
    width: 68px;
  }
}
.room-beds {
  flex: 1 1 192px;
  min-height: 192px;
  overflow-y: auto;
  background-color: hsla(30, 3%, 97%, 1);
}
.table-beds {
  width: 100%;
  table-layout: fixed;
  margin-bottom: 0;
  height: 100%;
}
.waiting {
  height: 150px;
  background-color: hsla(30, 3%, 97%, 1);
}
.waiting-content {
  height: 125px;
  overflow-y: auto;
}
.draggable-block-waiting {
  display: flex;
  flex-wrap: wrap;
  min-height: 110px;
}
.waiting-item {
  align-self: flex-start;
  flex: 0 1 143px;
}
.no-rooms {
  text-align: center;
  font-weight: bold;
}
.room-number {
  font-weight: bold;
  text-align: center;
  vertical-align: middle;
}
.beds {
  display: flex;
  flex-wrap: wrap;
}
.beds-item {
  flex: 1 1 33.3333%;
  display: flex;
  flex-wrap: nowrap;
  margin: 10px 0;
}

.without-doctor {
  margin: 7px auto;
  font-size: 12px;
}
.patient-row {
  display: flex;
}
.age {
  margin: 5px auto;
}

.chosen {
  &-unallocated-patient,
  &-doctor,
  &-attending-doctor,
  &-beds,
  &-patient-without-bed {
    background-color: transparent;
  }
}
.ghost {
  &-unallocated-patient,
  &-doctor,
  &-attending-doctor,
  &-beds,
  &-patient-without-bed {
    margin: 10px 5px;
    opacity: 0.5;
    background-color: #fff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    border-radius: 4px;
  }
  &-beds,
  &-doctor {
    background-color: #039372 !important;
    margin: 0
  }
}

.width80 {
  width: 80px;
}
</style>
