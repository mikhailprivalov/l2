<template>
  <tr :class="updated && 'has-success'">
    <td>{{ department.pk }}</td>
    <td>
      <input
        v-model="/* eslint-disable-line vue/no-mutating-props */ department.title"
        class="form-control"
        :disabled="!can_edit"
      >
    </td>
    <td>
      <input
        v-model="/* eslint-disable-line vue/no-mutating-props */ department.oid"
        class="form-control"
        placeholder="oid - подразделения"
        :disabled="!can_edit"
      >
    </td>
    <td>
      <Treeselect
        v-model="/* eslint-disable-line vue/no-mutating-props */ department.type"
        :multiple="false"
        :disable-branch-nodes="true"
        :options="types_options"
        placeholder="Тип не выбран"
        :clearable="false"
        :append-to-body="true"
        :disabled="!can_edit"
      />
    </td>
    <td>
      <div>
        <a
          href="#"
          class="a-under"
          style="padding-right: 10px"
          @click.prevent="editDepartment(department.pk)"
        >
          <i
            v-if="department.type === '7'"
            v-tippy
            class="fa fa-bed"
            style="margin-top: 10px; margin-left: 7px"
            title="Настройки подразделения"
          />
          <i
            v-if="department.type === '2'"
            v-tippy
            class="fa-solid fa-vials"
            style="margin-top: 10px; margin-left: 7px"
            title="Настройки подразделения"
          />
        </a>
      </div>
    </td>
    <SubGroupsDepartment
      v-if="subgroups_department"
      :department_pk="department.pk"
      :readonly="false"
    />
  </tr>
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import _ from 'lodash';

import departmentsDirectory from '@/api/departments-directory';
import * as actions from '@/store/action-types';
import SubGroupsDepartment from '@/modals/SubGroupDepartment.vue';

export default {
  name: 'DepartmentEditRow',
  components: { Treeselect, SubGroupsDepartment },
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
      subgroups_department: false,
    };
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
  created() {
    this.$root.$on('hide_subgroups_department', () => {
      this.subgroups_department = false;
    });
  },
  beforeMount() {
    clearTimeout(this.timer);
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
      const ok = await departmentsDirectory.sendDepartments({
        method: 'POST',
        hospital: this.selected_hospital,
        type: 'update',
        data: [
          {
            pk: this.department.pk,
            title: this.department_title,
            type: this.department_type,
            oid: this.department_oid,
          },
        ],
      });
      if (ok) {
        this.$root.$emit('msg', 'ok', 'Сохранено');
        this.updated = true;
        this.timer = setTimeout(() => {
          this.updated = false;
        }, 4000);
      } else {
        this.$root.$emit('msg', 'error', 'Ошибка');
      }

      await this.$store.dispatch(actions.GET_ALL_DEPARTMENTS);
    },
    editDepartment(iDdepartment) {
      this.subgroups_department = true;
    },
  },
};
</script>
