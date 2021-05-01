<template>
  <div style="max-width: 1024px;margin-top: 10px">
    <div class="input-group" style="margin-bottom: 10px">
      <span class="input-group-addon">Число колонок</span>
      <input type="number" class="form-control" v-model.number="columns.count"
             min="1" max="5" placeholder="Название колонки">
    </div>

    <table class="table table-bordered table-condensed" style="table-layout: fixed;">
      <colgroup>
        <col width="36">
        <col v-for="_ in columns.titles">
      </colgroup>
      <thead>
        <tr>
          <td></td>
          <td v-for="(_, i) in columns.titles" class="cl-td">
            <input type="text" class="form-control" v-model="columns.titles[i]">
          </td>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, j) in rows">
          <td class="cl-td">
            <button class="btn btn-blue-nb nbr" @click="deleteRow(j)" title="Удалить строку" v-tippy>
              <i class="fa fa-times"></i>
            </button>
          </td>
          <td v-for="(_, i) in columns.titles" class="cl-td">
            <input type="text" class="form-control" v-model="r[i]" placeholder="Значение по умолчанию">
          </td>
        </tr>
        <tr>
          <td :colspan="columns.count + 1">
            <button class="btn btn-blue-nb" @click="addRow">добавить строку</button>
          </td>
        </tr>
      </tbody>
    </table>

    <label>
      <input type="checkbox" v-model="dynamicRows" /> пользователь может менять число строк
    </label>
  </div>
</template>
<script>
import _ from 'lodash';

const DEFAULT_TITLES = [
  'Колонка 1',
  'Колонка 2',
];

const DEFAULT_ROWS = [
  [
    '',
    '',
  ]
];

export default {
  name: 'TableConstructor',
  props: {
    row: {}
  },
  mounted() {
    this.checkTable();
  },
  data() {
    return {
      columns: {
        count: 2,
        titles: DEFAULT_TITLES,
      },
      rows: DEFAULT_ROWS,
      dynamicRows: true,
    };
  },
  computed: {
    columnsCount() {
      return this.columns.count;
    },
    result() {
      return {
        columns: this.columns,
        rows: this.rows,
        dynamicRows: this.dynamicRows,
      };
    },
  },
  watch: {
    columnsCount() {
      this.validate();
    },
    result: {
      deep: true,
      handler() {
        this.row.values_to_input = [
          JSON.stringify(this.result),
        ];
      },
    },
  },
  methods: {
    checkTable() {
      let params = this.row.values_to_input[0] || '{}';
      try {
        params = JSON.parse(params);
      } catch (e) {
        params = {};
      }

      params.columns = params.columns || this.columns;
      params.rows = params.rows || this.rows;
      params.dynamicRows = Boolean(params.dynamicRows || this.dynamicRows);

      if (!_.isObject(params.columns)) {
        params.columns = {};
      }

      params.columns.count = Number(params.columns.count || 2);

      if (!Array.isArray(params.columns.titles)) {
        params.columns.titles = DEFAULT_TITLES;
      }

      if (!Array.isArray(params.rows)) {
        params.rows = DEFAULT_ROWS;
      }

      params.rows = params.rows.filter(r => Array.isArray(r) && r.every(v => _.isString));

      if (params.rows.length === 0) {
        params.rows = DEFAULT_ROWS;
      }

      this.columns = params.columns;
      this.rows = params.rows;

      this.validate();
    },
    addRow() {
      this.rows.push([]);
      this.validateRowsLength();
    },
    deleteRow(i) {
      this.rows.splice(i, 1);
    },
    validate() {
      this.validateColumnsLength();
      this.validateRowsLength();
    },
    validateColumnsLength() {
      if (this.columns.count > 5) {
        this.columns.count = 5;
      } else if (this.columns.count === 0) {
        this.columns.count = 1;
      }
      const c = this.columns.count;
      if (this.columns.titles.length < c) {
        for (let i = 0; i < c - this.columns.titles.length; i++) {
          this.columns.titles.push(`Колонка ${this.columns.titles.length + 1}`);
        }
      } else if (this.columns.titles.length > c) {
        this.columns.titles.splice(c);
      }
    },
    validateRowsLength() {
      const c = this.columns.count;
      for (const r of this.rows) {
        if (r.length < c) {
          for (let i = 0; i < c - r.length; i++) {
            r.push('');
          }
        } else if (r.length > c) {
          r.splice(c);
        }
      }
    },
  },
}
</script>

<style scoped lang="scss">

</style>
