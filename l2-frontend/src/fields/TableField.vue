<template>
  <div style="max-width: 1024px;">
    <table class="table table-bordered table-condensed" style="table-layout: fixed;" v-if="settings">
      <colgroup>
        <col width="36" v-if="params.dynamicRows && !disabled">
        <col v-for="(_, i) in params.columns.titles" :key="i" :width="settings[i].width">
      </colgroup>
      <thead>
      <tr>
        <td v-if="params.dynamicRows && !disabled"></td>
        <th v-for="(t, i) in params.columns.titles" :key="i">
          {{ t }}
        </th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(r, j) in rows" :key="j">
        <td class="cl-td" v-if="params.dynamicRows && !disabled">
          <button class="btn btn-blue-nb nbr" @click="deleteRow(j)" title="Удалить строку" v-tippy>
            <i class="fa fa-times"></i>
          </button>
        </td>
        <td v-for="(_, i) in params.columns.titles" :key="i" class="cl-td">
          <div v-if="settings[i].type === 'rowNumber' || disabled" class="just-val"
               :class="settings[i].type === 'rowNumber' && 'rowNumber'">
            {{ r[i] }}
          </div>
          <template v-else-if="settings[i].type === 0">
            <textarea :rows="settings[i].lines" class="form-control"
                      v-if="settings[i].lines > 1" v-model="r[i]"></textarea>
            <input class="form-control" v-else v-model="r[i]"/>
          </template>
          <DateFieldWithNow v-else-if="settings[i].type === 1" v-model="r[i]"/>
          <SelectField :variants="settings[i].variants" class="form-control fw"
                       v-else-if="settings[i].type === 10" v-model="r[i]"/>
          <RadioField :variants="settings[i].variants"
                      v-else-if="settings[i].type === 12" v-model="r[i]"/>
          <input class="form-control" v-else-if="settings[i].type === 18" v-model="r[i]" type="number"/>
        </td>
      </tr>
      <tr v-if="params.dynamicRows && !disabled">
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
import SelectField from '@/fields/SelectField.vue';
import RadioField from '@/fields/RadioField.vue';
import DateFieldWithNow from '@/fields/DateFieldWithNow.vue';

const DEFAULT_SETTINGS = () => ({
  type: 0,
  lines: 1,
  variants: '',
  width: '',
});

export default {
  name: 'TableField',
  components: { DateFieldWithNow, RadioField, SelectField },
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
          settings: [],
        },
        dynamicRows: true,
      },
      rows: [],
    };
  },
  computed: {
    result() {
      return {
        columns: {
          titles: this.params.columns.titles,
          settings: this.settings.map((s) => _.pick(s, ['type', 'width'])),
        },
        rows: this.rows,
      };
    },
    settings() {
      return this.params.columns.settings || [];
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
    event: 'modified',
  },
  methods: {
    changeValue(newVal) {
      this.$emit('modified', newVal);
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

      value = { ...params, ...value };

      if (!Array.isArray(value.rows)) {
        value.rows = params.rows;
      }

      if (!Array.isArray(params.settings)) {
        params.settings = [];
      }

      for (let i = 0; i < Math.max(params.columns.count - params.columns.settings.length, 0); i++) {
        params.columns.settings.push({});
      }

      for (let i = 0; i < params.columns.settings.length; i++) {
        const s = params.columns.settings[i];
        params.columns.settings[i] = { ...DEFAULT_SETTINGS(), ...s };
      }

      value.rows = value.rows.filter((r) => Array.isArray(r) && r.every((v) => _.isString(v)));

      this.params = params;
      this.rows = value.rows;

      this.validate();
    },
    addRow() {
      this.rows.push([]);
      this.validate();
    },
    deleteRow(i) {
      this.rows.splice(i, 1);
      this.validate();
    },
    validate() {
      this.validateRowsLength();
      this.validateRowsValues();
    },
    validateRowsValues() {
      for (let i = 0; i < this.settings.length; i++) {
        const t = this.settings[i].type;

        if (t === 'rowNumber') {
          for (let j = 0; j < this.rows.length; j++) {
            const r = this.rows[j];
            r[i] = `${j + 1}`;
          }
        } else if (t === 10 || t === 12) {
          const v = (this.settings[i].variants || '').split('\n');
          for (let j = 0; j < this.rows.length; j++) {
            const r = this.rows[j];

            if (!v.includes(r[i])) {
              // eslint-disable-next-line prefer-destructuring
              r[i] = v[0];
            }
          }
        }
      }
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
};
</script>

<style scoped lang="scss">
.just-val {
  padding: 5px;
}

.rowNumber {
  font-weight: bold;
}
</style>
