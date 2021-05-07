<template>
  <tr :class="updated && 'has-success'">
    <td>{{ department.pk }}</td>
    <td><input class="form-control" v-model="department.title" :disabled="!can_edit"/></td>
    <td><input class="form-control" placeholder="oid - подразделения" v-model="department.oid" :disabled="!can_edit"/></td>
    <td>
      <treeselect :multiple="false" :disable-branch-nodes="true" :options="types_options"
                  placeholder="Тип не выбран" v-model="department.type"
                  :clearable="false"
                  :append-to-body="true"
                  :disabled="!can_edit"
      />
    </td>
    <td>
      <i v-if="department.type ==='7'" class="fa fa-bed" style="margin-top: 10px; margin-left: 7px"/>
    </td>
  </tr>
</template>
<script>

import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import departments_directory from '@/api/departments-directory';
import _ from 'lodash';
import * as actions from '../store/action-types';

export default {
  name: 'DepartmentEditRow',
  components: { Treeselect },
  props: {
    can_edit: {
      type: Boolean,
    },
    selected_hospital: {
      type: Number,
    },
    department: {
      type: Object,
    },
    types_options: {
      type: Array,
    },
  },
  data() {
    return {
      updated: false,
      timer: null,
    };
  },
  beforeMount() {
    clearTimeout(this.timer);
  },
  watch: {
    department_title() {
      this.save_clear_deb();
    },
    department_type() {
      this.save_clear_deb();
    },
    department_oid() {
      this.save_clear_deb();
    },
  },
  computed: {
    department_title() {
      return this.department.title;
    },
    department_type() {
      return this.department.type;
    },
    department_oid() {
      return this.department.oid;
    },
  },
  methods: {
    save_clear_deb() {
      this.updated = false;
      this.save_deb();
    },
    save_deb: _.debounce(function () {
      this.save();
    }, 300),
    async save() {
      const ok = await departments_directory.sendDepartments({
        method: 'POST',
        hospital: this.selected_hospital,
        type: 'update',
        data: [{
          pk: this.department.pk, title: this.department_title, type: this.department_type, oid: this.department_oid,
        }],
      });
      if (ok) {
        window.okmessage('Сохранено');
        this.updated = true;
        this.timer = setTimeout(() => {
          this.updated = false;
        }, 4000);
      } else {
        window.errmessage('Ошибка');
      }

      await this.$store.dispatch(actions.GET_ALL_DEPARTMENTS);
    },
  },
};
</script>
