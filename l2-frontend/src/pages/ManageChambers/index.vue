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
          <draggable
            v-model="unallocatedPatients"
            :options="{group:{ name: 'unallocatedPatients', put: 'beds.contents'}, sort: false, ForceFallback: true}"
            class="patient"
            chosen-class="dragClass"
            animation="500"
            @change="extractPatientBed"
          >
            <div
              v-for="patient in unallocatedPatients"
              :key="patient.pk"
              class="patient-content"
            >
              {{ patient.fio }}
            </div>
          </draggable>
        </div>
      </div>
    </div>
    <div>
      <table class="table table-fixed table-bordered table-responsive table-condensed chamber-table">
        <colgroup>
          <col width="80">
          <col width="670">
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
              >
                <draggable
                  v-model="bed.contents"
                  :options="{group: { name: 'beds.contents', put: bed.contents < 1, pull: 'unallocatedPatients'}, sort: false}"
                  animation="500"
                  class="drag-and-drop-element"
                  @change="entrancePatientBed($event, bed)"
                >
                  <div
                    class="element"
                    @click="showModal = bed.pk"
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
                <span
                  v-if="bed.contents.length > 0"
                  class="element-fio"
                >
                  {{ bed.contents[0].short_fio }}
                </span>
                <Modal
                  v-if="showModal === bed.pk"
                  ref="modal"
                  :z-index="5001"
                  white-bg="true"
                  max-width="710px"
                  width="100%"
                  show-footer="true"
                  @close="showModal = ''"
                >
                  <span slot="header">Информация по пациенту</span>
                  <div slot="body">
                    <table class="table table-bordered ">
                      <colgroup>
                        <col width="124">
                        <col>
                      </colgroup>
                      <tbody>
                        <tr>
                          <td class="table-header-row">
                            Лечащий врач
                          </td>
                          <td class="table-content-row">
                            <FiltersDoc
                              :doctors="doctors"
                              :filters="filters"
                            />
                          </td>
                        </tr>
                        <tr>
                          <td
                            class="table-header-row"
                          >
                            ФИО:
                          </td>
                          <td
                            v-if="bed.contents.length > 0"
                            class="table-content-row"
                          >
                            {{ bed.contents[0].fio }}
                          </td>
                        </tr>
                        <tr>
                          <td class="table-header-row">
                            Возраст:
                          </td>
                          <td
                            v-if="bed.contents.length > 0"
                            class="table-content-row"
                          >
                            {{ bed.contents[0].age }} лет
                          </td>
                        </tr>
                        <tr>
                          <td class="table-header-row">
                            Пол:
                          </td>
                          <td
                            v-if="bed.contents.length > 0"
                            class="table-content-row"
                          >
                            {{ bed.contents[0].sex }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div slot="footer">
                    <button
                      class="btn btn-primary-nb btn-blue-nb"
                      type="button"
                      @click="showModal = ''"
                    >
                      Закрыть
                    </button>
                  </div>
                </Modal>
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
  </div>
</template>

<script lang="ts">
import draggable from 'vuedraggable';

import usersPoint from '@/api/user-point';
import Modal from '@/ui-cards/Modal.vue';

import Filters from './components/Filters.vue';
import FiltersDoc from './components/FiltersDoc.vue';

export default {
  name: 'ManageChambers',
  components: {
    Filters,
    draggable,
    FiltersDoc,
    Modal,
  },
  data() {
    return {
      chambers: [],
      departments: [],
      unallocatedPatients: [],
      doctors: [],
      showModal: '',
      filters: {
        department_pk: -1,
        doctor_pk: -1,
      },
    };
  },
  computed: {
    department() {
      return this.filters.department_pk;
    },
  },
  watch: {
    department() {
      this.getUnallocatedPatients();
      this.loadChamberAndBed();
    },
  },
  mounted() {
    this.init();
  },
  methods: {
    async init() {
      const { data } = await this.$api('procedural-list/suitable-departments');
      this.departments = [{ id: -1, label: 'Отделение не выбрано' }, ...data];
    },
    async getDoctors(doc) {
      const { users } = await usersPoint.loadUsersByGroup({ group: ['Лечащий врач'] });
      this.doctors = [{ id: doc.id, label: doc.label }, ...users];
      console.log(this.doctors);
    },
    async getUnallocatedPatients() {
      const row = await this.$api('chambers/get-unallocated-patients', {
        department_pk: this.department,
      });
      this.unallocatedPatients = row.data;
    },
    async loadChamberAndBed() {
      const row = await this.$api('chambers/get-chambers-and-beds', {
        department_pk: this.department,
      });
      this.chambers = row.data;
    },
    async entrancePatientBed({ added }, bed) {
      if (added) {
        const ok = await this.$api('chambers/entrance-patient-to-bed', {
          beds: bed,
        });
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Пациент поступил');
        }
      }
    },
    async extractPatientBed({ added }) {
      if (added) {
        const ok = await this.$api('chambers/extract-patient-bed', {
          patient: added.element,
        });
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Пациент выписан');
        }
      }
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
.patient {
  padding: 5px;
  margin: 10px;
  height: calc(100vh - 100px);
}
.chamber-table {
  position: absolute;
  top: 35px;
  right: 0;
  bottom: 0;
  left: 300px;
  width: 750px;
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
.drag-and-drop-element {
  display: inline-block;
  overflow: hidden;
  background-color: #fff;
  margin-left: 20px;
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
.patient-content {
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

</style>
