<template>
  <div style="max-width: 1024px">
    <div
      class="input-group"
      style="margin-top: 10px"
    >
      <span class="input-group-addon">Подразделение</span>
      <div
        class="input-group-btn"
        style="width: 100%;"
      >
        <TreeSelectFieldById
          v-model="department"
          :variants="departmentsForSelect"
        />
      </div>
    </div>
    <div
      class="input-group"
      style="margin-top: 10px"
    >
      <span class="input-group-addon">Группы пользователей</span>
      <div
        class="input-group-btn"
        style="width: 100%;"
      >
        <TreeSelectFieldMultiById
          v-model="userGroups"
          :variants="totalGroupsForSelect"
        />
      </div>
    </div>
    <div
      class="input-group"
      style="margin-top: 10px"
    >
      <span class="input-group-addon">Тип значения</span>
      <div
        class="input-group-btn"
        style="width: 100%;"
      >
        <TreeSelectFieldById
          v-model="valueType"
          :variants="COLUMN_TYPES"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { mapGetters } from 'vuex';
import { debounce } from 'lodash/function';

import TreeSelectFieldById from '@/fields/TreeSelectFieldById.vue';
import TreeSelectFieldMultiById from '@/fields/TreeSelectFieldMultiById.vue';

const COLUMN_TYPES = [
  [0, 'Текст'],
  [18, 'Число'],
];

const valueOrDefault = (value, defaultValue) => {
  if (value === undefined) {
    return defaultValue;
  }
  return value;
};

export default {
  name: 'RelationalTableConstructor',
  components: {
    TreeSelectFieldById,
    TreeSelectFieldMultiById,
  },
  props: {
    row: {},
  },
  data() {
    return {
      department: null,
      userGroups: [],
      valueType: COLUMN_TYPES[0][0],
      COLUMN_TYPES: COLUMN_TYPES.map(([id, label]) => ({
        id,
        label,
      })),
    };
  },
  computed: {
    ...mapGetters({
      departments: 'allDepartments',
      totalGroups: 'totalGroups',
    }),
    departmentsForSelect() {
      return this.departments.map((d) => ({
        id: d.pk,
        label: d.title,
      }));
    },
    totalGroupsForSelect() {
      return this.totalGroups.map((d) => ({
        id: d.pk,
        label: d.title,
      }));
    },
    result() {
      return {
        department: this.department,
        userGroups: [...this.userGroups],
        valueType: this.valueType,
      };
    },
  },
  watch: {
    result: {
      deep: true,
      handler() {
        this.updateValue();
      },
    },
    departmentsForSelect: {
      immediate: true,
      handler() {
        if (this.department === null && this.departmentsForSelect.length > 0) {
          this.department = this.departmentsForSelect[0].id;
        }
      },
    },
  },
  mounted() {
    this.checkTable();
  },
  methods: {
    updateValue: debounce(function () {
      // eslint-disable-next-line vue/no-mutating-props
      this.row.values_to_input = [JSON.stringify(this.result)];
    }, 100),
    checkTable() {
      let params = this.row.values_to_input[0] || '{}';
      try {
        params = JSON.parse(params);
      } catch (e) {
        params = {};
      }

      params.department = valueOrDefault(params.department, this.department);
      params.userGroups = valueOrDefault(params.userGroups, this.userGroups);
      params.valueType = valueOrDefault(params.valueType, this.valueType);

      if (!Array.isArray(params.userGroups)) {
        params.userGroups = [];
      }

      this.department = params.department;
      this.userGroups = params.userGroups;
      this.valueType = params.valueType;
    },
  },
};
</script>
