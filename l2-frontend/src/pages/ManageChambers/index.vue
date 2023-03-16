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
        <div class="sidebar-content">
          <draggable
            :list="users"
            group="my-group"
          >
            <div
              v-for="user in users"
              :key="user.pk"
              class="research"
            >
              {{ user.fio }} {{ user.age }}
            </div>
          </draggable>
        </div>
      </div>
    </div>
    <div>
      <table class="table table-fixed table-bordered table-responsive table-condensed chamber-table">
        <colgroup>
          <col width="250">
          <col width="500">
        </colgroup>
        <thead>
          <tr>
            <th>Название палаты</th>
            <th>Управление койками</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="chamber in chambers"
            :key="chamber.pk"
          >
            <td>
              {{ chamber.label }}
            </td>
            <td>
              <draggable
                :list="beds"
                group="my-group"
              >
                <div
                  v-for="bed in beds"
                  v-if="chamber.pk === bed.pk_chamber || bed.age.length !== 0"
                  :key="bed.pk"
                >
                  <i
                    class="fa fa-bed"
                    style="margin-top: 10px; margin-left: 25px; font-size: 30px;"
                  />
                  {{ bed.age }}
                </div>
              </draggable>
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

import Filters from './components/Filters.vue';

export default {
  name: 'ManageChambers',
  components: { Filters, draggable },
  data() {
    return {
      beds: [],
      chambers: [],
      departments: [],
      users: [],
      listUsers: [],
      listBeds: [],
      filters: {
        department_pk: -1,
      },
    };
  },
  computed: {
    deapartment() {
      return this.filters.department_pk;
    },
  },
  watch: {
    deapartment() {
      this.loadUser();
      this.loadChamber();
      this.loadBed();
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
    async loadUser() {
      const result = await this.$api('chambers/all-patients', {
        department_pk: this.deapartment,
      });
      this.users = result.data;
    },
    async loadChamber() {
      const result = await this.$api('chambers/get-chambers', {
        department_pk: this.deapartment,
      });
      this.chambers = result.data;
    },
    async loadBed() {
      const list = await this.$api('chambers/get-beds', {
        department_pk: this.deapartment,
      });
      this.beds = list.data;
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

  display: flex;
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
.research {
  background-color: #fff;
  padding: 5px;
  margin: 10px;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;

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

.research:not(:first-child) {
  margin-top: 0;
}

.research:last-child {
  margin-bottom: 0;
}
.chamber-table {
  position: absolute;
  top: 35px;
  right: 0;
  bottom: 0;
  left: 300px;
  width: 750px;
}
</style>
