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
          <h5 style="text-align: center">
            Пациенты
          </h5>
          <draggable
            v-model="unallocatedPatients"
            :options="{group:{ name: 'unallocatedPatients', put: 'patient'}, sort: false, ForceFallback: true}"
            class="draggable-element"
            chosen-class="dragClass"
            animation="500"
            @change="extractPatientBed"
          >
            <div
              v-for="patient in unallocatedPatients"
              :key="patient.pk"
              class="content-research"
            >
              {{ patient.fio }}
            </div>
          </draggable>
        </div>
      </div>
    </div>
    <div class="construct-bottom-root">
      <div class="construct-bottom-bar">
        <div class="sidebar-content">
          <h5 style="text-align: center">
            Дома
          </h5>
          <draggable
            v-model="attendingDoctor"
            :options="{group:{
                         name: 'PatientWithoutBeds',
                         pull: ['unallocatedPatients', 'patient'],
                         put: ['unallocatedPatients', 'patient']},
                       sort: false,
                       ForceFallback: true}"
            class="draggable-element"
            animation="500"
          />
        </div>
      </div>
    </div>
    <div class="scroll-div">
      <table class="table table-fixed table-bordered table-responsive table-condensed chamber-table">
        <colgroup>
          <col width="80">
          <col width="856">
        </colgroup>
        <thead>
          <tr>
            <th
              class="header-alignment"
            >
              Номер палаты
            </th>
            <th>Управление койками</th>
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
            <td class="drop-and-drag-zone">
              <div
                v-for="bed in chamber.beds"
                :key="bed.pk"
                class="element"
                :class="{ 'padding-element': bed.contents.length < 1}"
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
                  v-model="bed.contents"
                  :options="{
                    group:{
                      name: 'patient',
                      put: 'patient' || 'unallocatedPatients',
                      pull: 'unallocatedPatients' || 'patient'
                    },
                    sort: false}"
                  animation="500"
                  class="drag-and-drop-patient"
                  @change="entrancePatientBed($event, bed)"
                  @remove="clearArrayDoctor(bed)"
                >
                  <div
                    style="display: inline-block"
                  >
                    <div
                      v-if="bed.contents.length > 0"
                      class="element-content"
                    >
                      {{ bed.contents[0].age }}л.
                    </div>
                    <i
                      class="fa fa-bed bedMin"
                      :class="{ 'women': colorWomen(bed), 'man': colorMan(bed) }"
                    />
                  </div>
                </draggable>
                <table
                  v-if="bed.contents.length > 0 || bed.doctor.length > 0"
                  class="table table-fixed table-bordered table-responsive table-condensed table-info"
                >
                  <tr>
                    <td
                      v-if="bed.contents.length > 0"
                    >
                      {{ bed.contents[0].short_fio }}
                    </td>
                  </tr>
                  <tr>
                    <td
                      style="border-top: 2px solid #ddd;"
                    >
                      <div v-if="bed.doctor.length > 0 && bed.contents.length > 0">
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
          <h5 style="text-align: center">
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
            >
              {{ doctor.fio }}
            </div>
          </draggable>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import draggable from 'vuedraggable';

import * as actions from '@/store/action-types';

import Filters from './components/Filters.vue';
import FiltersDoc from './components/FiltersDoc.vue';

export default {
  name: 'ManageChambers',
  components: {
    Filters,
    draggable,
    FiltersDoc,
  },
  data() {
    return {
      chambers: [],
      departments: [],
      unallocatedPatients: [],
      attendingDoctor: [],
      filters: {
        department_pk: -1,
        departmentDoc_pk: -1,
      },
    };
  },
  computed: {
    department() {
      return this.filters.department_pk;
    },
    departmentDoc() {
      return this.filters.departmentDoc_pk;
    },
  },
  watch: {
    department() {
      this.getUnallocatedPatients();
      this.loadChamberAndBed();
    },
    departmentDoc() {
      this.getAttendingDoctor();
    },
  },
  mounted() {
    this.init();
  },
  methods: {
    async init() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { data } = await this.$api('procedural-list/suitable-departments');
      this.departments = [{ id: -1, label: 'Отделение не выбрано' }, ...data];
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async getAttendingDoctor() {
      await this.$store.dispatch(actions.INC_LOADING);
      const row = await this.$api('chambers/get-attending-doctor', {
        department_pk: this.departmentDoc,
      });
      this.attendingDoctor = row.data;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async getUnallocatedPatients() {
      await this.$store.dispatch(actions.INC_LOADING);
      const row = await this.$api('chambers/get-unallocated-patients', {
        department_pk: this.department,
      });
      this.unallocatedPatients = row.data;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async loadChamberAndBed() {
      await this.$store.dispatch(actions.INC_LOADING);
      const row = await this.$api('chambers/get-chambers-and-beds', {
        department_pk: this.department,
      });
      this.chambers = row.data;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async entrancePatientBed({ added }, bed) {
      if (added) {
        await this.$store.dispatch(actions.INC_LOADING);
        const ok = await this.$api('chambers/entrance-patient-to-bed', {
          beds: bed,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Пациент поступил');
        }
      }
    },
    async extractPatientBed({ added }) {
      if (added) {
        await this.$store.dispatch(actions.INC_LOADING);
        const ok = await this.$api('chambers/extract-patient-bed', {
          patient: added.element,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Пациент выписан');
        }
      }
    },
    async changeDoctor({ added, removed }, bed) {
      if (added) {
        await this.$store.dispatch(actions.INC_LOADING);
        const ok = await this.$api('chambers/doctor-assigned-patient', {
          beds: bed,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Лечащий врач закреплен');
        }
      }
      if (removed) {
        await this.getAttendingDoctor();
        await this.$store.dispatch(actions.INC_LOADING);
        const ok = await this.$api('chambers/doctor-detached-patient', {
          doctor: removed.element,
          beds: bed,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Лечащий врач откреплен');
        }
      }
    },
    conditionsDragDoc(bed) {
      if (bed.contents.length > 0 && bed.doctor.length < 1) {
        return 'attendingDoctor';
      }
      return false;
    },
    conditionsDragBed(bed) {
      if (bed.contents < 1) {
        return 'unallocatedPatients';
      }
      return false;
    },
    clearArrayDoctor(bed) {
      bed.doctor.pop();
    },
    colorWomen(val) {
      if (val.contents.length > 0) {
        return val.contents[0].sex === 'ж';
      }
      return false;
    },
    colorMan(val) {
      if (val.contents.length > 0) {
        return val.contents[0].sex === 'м';
      }
      return false;
    },
  },
};
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
  width: 936px;
  height: 500px;
}
.construct-right {
  position: absolute;
  top: 35px;
  right: 0;
  bottom: 0;
  left: 1236px;
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
.construct-bottom-bar {
  width: 936px;
  display: flex;
  flex-direction: column;

  .form-control {
    border-radius: 0;
    border-top: none;
    border-left: none;
    border-right: none;
  }
}
.construct-sidebar {
  width: 299px;
  border-right: 1px solid #b1b1b1;
  display: flex;
  flex-direction: column;

  .form-control {
    border-radius: 0;
    border-top: none;
    border-left: none;
    border-right: none;
  }
}
.sidebar-content {
  height: 100%;
  overflow-y: auto;
  background-color: hsla(30, 3%, 97%, 1);
}
.draggable-element {
  padding: 5px;
  margin: 10px;
  height: 615px;
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
.drop-and-drag-zone {
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
.table-tippy {
  table-layout: fixed;
  padding: 0;
  margin: 5px 0 0;
}
.table-header-row {
  font-weight: 600;
  overflow: hidden;
  vertical-align: middle;
}
.table-content-row:not(.cl-td) {
  overflow: hidden;
  vertical-align: middle;
}
.inner {
  height: 50px;
  overflow-y: auto;
  overflow-x: hidden;
}
.element-fio {
  display: inline-block;
  font-size: 12px;
  vertical-align: top;
  margin-top: 10px;
}
.div-tippy {
  max-width: 450px;
  //height: 450px;
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
</style>
