<template>
  <div style="max-width: 1024px;">
    <table class="table table-bordered table-condensed" style="table-layout: fixed;">
      <colgroup>
        <col width="36" v-if="params.dynamicRows">
        <col v-for="_ in params.columns.titles">
      </colgroup>
      <thead>
      <tr>
        <td v-if="params.dynamicRows"></td>
        <th v-for="t in params.columns.titles">
          {{t}}
        </th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(r, j) in rows">
        <td class="cl-td" v-if="params.dynamicRows">
          <button class="btn btn-blue-nb nbr" @click="deleteRow(j)" title="Удалить строку" v-tippy>
            <i class="fa fa-times"></i>
          </button>
        </td>
        <td v-for="(_, i) in params.columns.titles" class="cl-td">
          <input type="text" class="form-control" v-model="r[i]" placeholder="Значение по умолчанию">
        </td>
      </tr>
      <tr v-if="params.dynamicRows">
        <td :colspan="params.columns.count + 1">
          <button class="btn btn-blue-nb" @click="addRow">добавить строку</button>
        </td>
      </tr>
      </tbody>
    </table>
  </div>
</template>
<script>
import _ from 'lodash';

export default {
  name: 'TableField',
  props: {
    value: {
      required: false,
    },
    variants: {
      required: true,
    },
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
  },
  mounted() {
    this.checkTable();
  },
  data() {
    return {
      params: {
        columns: {
          count: 2,
          titles: [],
        },
        dynamicRows: true,
      },
      rows: [],
    };
  },
  computed: {
    result() {
      return {
        columns: this.params.columns,
        rows: this.rows,
      };
    },
  },
  watch: {
    result: {
      deep: true,
      handler() {
        this.changeValue(JSON.stringify(this.result));
      },
    },
  },
  model: {
    event: `modified`
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal)
    },
    checkTable() {
      let params = this.variants[0] || '{}';
      let value = this.value || '{}';
      try {
        params = JSON.parse(params);
      } catch (e) {
        params = {};
      }
      try {
        value = JSON.parse(value);
      } catch (e) {
        value = {};
      }

      value = {...params, ...value};

      if (!Array.isArray(value.rows)) {
        value.rows = params.rows;
      }

      value.rows = value.rows.filter(r => Array.isArray(r) && r.every(v => _.isString));

      this.params = params;
      this.rows = value.rows;

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
      this.validateRowsLength();
    },
    validateRowsLength() {
      const c = this.params.columns.count;
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
