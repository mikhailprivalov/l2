<template>
  <div>
    <div class="card-no-hover card card-1 filters">
      <treeselect :multiple="false" :disable-branch-nodes="true"
                  :options="can_edit_any_organization ? all_hospitals_with_none : own_hospital"
                  placeholder="Больница не выбрана" v-model="selected_hospital"
                  :append-to-body="true"
                  :clearable="false"
      />
    </div>

    <table class="table table-bordered table-responsive">
      <colgroup>
        <col width="40">
        <col width="500">
        <col>
        <col width="300">
        <col width="50">
      </colgroup>
      <tbody>
      <DepartmentEditRow :can_edit="can_edit" :department="department" :types_options="types_options"
                         :selected_hospital="selected_hospital"
                         v-for="department in departments" :key="department.pk"/>
      <tr v-if="can_edit">
        <td></td>
        <td><input type="text" class="form-control" placeholder="Название" v-model="create.title"></td>
        <td>
          <treeselect :multiple="false" :disable-branch-nodes="true" :options="types_options"
                      placeholder="Тип не выбран" v-model="create.type"
                      :clearable="false"
                      :append-to-body="true"
          />
          <br/>
          <input type="button" class="btn btn-primary-nb form-control" @click="insert" value="Добавить"
                 style="margin-top: 15px" :disabled="!create_valid">
        </td>
      </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import departments_directory from '@/api/departments-directory';
import { mapGetters } from 'vuex';
import DepartmentEditRow from '@/forms/DepartmentEditRow.vue';
import * as actions from '../store/action-types';

export default {
  components: { DepartmentEditRow, Treeselect },
  name: 'departments-form',
  data() {
    return {
      create: {
        title: '',
        type: '0',
      },
      selected_hospital: -1,
      departments: [],
    };
  },
  watch: {
    user_hospital: {
      handler() {
        if (this.user_hospital === -1) {
          return;
        }
        this.selected_hospital = this.user_hospital;
      },
      immediate: true,
    },
    selected_hospital() {
      if (this.user_hospital === -1) {
        return;
      }

      this.loadDepartments();
    },
  },
  methods: {
    async insert() {
      if (!this.create_valid) return;
      await this.$store.dispatch(actions.INC_LOADING);
      const ok = await departments_directory.sendDepartments({
        method: 'POST',
        hospital: this.selected_hospital,
        type: 'insert',
        data: [{ pk: -1, title: this.create.title, type: this.create.type }],
      });

      await this.loadDepartments();
      await this.$store.dispatch(actions.DEC_LOADING);

      if (ok) {
        this.create.title = '';
        window.okmessage('Сохранено');
      } else {
        window.errmessage('Ошибка');
      }
    },
    async loadDepartments() {
      await this.$store.dispatch(actions.INC_LOADING);
      this.departments = (await departments_directory.getDepartments({
        method: 'GET',
        hospital: this.selected_hospital,
        withoutDefault: true,
      })).departments;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
  computed: {
    can_edit() {
      return this.$store.getters.canEditDepartments;
    },
    types() {
      return this.$store.getters.allTypes;
    },
    types_options() {
      const r = [];
      for (const row of this.types) {
        r.push({ label: row.title, id: row.pk });
      }
      return r;
    },
    trim_title() {
      return this.create.title.trim();
    },
    create_valid() {
      return this.trim_title.length > 0;
    },
    ...mapGetters(['user_data', 'hospitals', 'all_hospitals_with_none']),
    can_edit_any_organization() {
      return this.user_data.su;
    },
    user_hospital() {
      return this.user_data.hospital || -1;
    },
    own_hospital() {
      return [this.hospitals.find(({ id }) => id === this.user_data.hospital) || {}];
    },
  },
};
</script>

<style scoped lang="scss">
.filters {
  padding: 10px;
  margin: 0 0 15px 0;
}
</style>
