<template>
  <div style="max-width: 1024px;">
    <table class="table table-bordered table-condensed" style="table-layout: fixed;" v-if="settings">
      <colgroup>
        <col width="36" v-if="params.dynamicRows && !disabled" />
        <col v-for="(_, i) in params.columns.titles" :key="i" :width="settings[i].width" />
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
          <td v-for="(_, i) in params.columns.titles" :key="i" class="cl-td" :class="settings[i].type === 2 && 'mkb'">
            <div
              v-if="settings[i].type === 'rowNumber' || disabled"
              class="just-val"
              :class="settings[i].type === 'rowNumber' && 'rowNumber'"
            >
              {{ r[i] }}
            </div>
            <template v-else-if="settings[i].type === 0">
              <textarea
                :rows="settings[i].lines"
                class="form-control"
                :class="errors[`${fieldPk}_${j}_${i}`] && 'has-error-field'"
                v-if="settings[i].lines > 1"
                v-model="r[i]"
              ></textarea>
              <input class="form-control" :class="errors[`${fieldPk}_${j}_${i}`] && 'has-error-field'" v-else v-model="r[i]" />
            </template>
            <DateFieldWithNow v-else-if="settings[i].type === 1" v-model="r[i]" />
            <SelectField
              :variants="settings[i].variants"
              class="form-control fw"
              :class="errors[`${fieldPk}_${j}_${i}`] && 'has-error-field'"
              v-else-if="settings[i].type === 10"
              v-model="r[i]"
            />
            <RadioField :variants="settings[i].variants" v-else-if="settings[i].type === 12" v-model="r[i]" />
            <input
              class="form-control"
              :class="errors[`${fieldPk}_${j}_${i}`] && 'has-error-field'"
              v-else-if="settings[i].type === 18"
              v-model="r[i]"
              type="number"
            />
            <MKBFieldForm
              v-else-if="settings[i].type === 2"
              :classes="errors[`${fieldPk}_${j}_${i}`] ? 'has-error-field' : ''"
              :short="false"
              v-model="r[i]"
            />
            <MKBFieldTreeselect
              v-else-if="settings[i].type === 33"
              :class="errors[`${fieldPk}_${j}_${i}`] && 'has-error-field'"
              v-model="r[i]"
              @modified="changeCell(j, i, $event)"
              dictionary="mkb10.5"
            />
            <MKBFieldTreeselect
              v-else-if="settings[i].type === 32"
              :class="errors[`${fieldPk}_${j}_${i}`] && 'has-error-field'"
              v-model="r[i]"
              @modified="changeCell(j, i, $event)"
              dictionary="mkb10.6"
            />
            <SearchFieldValueField
              v-else-if="settings[i].type === 23"
              :readonly="false"
              :field-pk-initial="r[i]"
              :client-pk="card_pk"
              :lines="1"
              :raw="true"
              :not_autoload_result="false"
              :iss_pk="iss_pk"
              v-model="r[i]"
              :once="true"
            />

            <div v-if="errors[`${fieldPk}_${j}_${i}`]" class="has-error-message">
              {{ errors[`${fieldPk}_${j}_${i}`] }}
            </div>
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
<script lang="ts">
import _ from 'lodash';
import { debounce } from 'debounce';
import SelectField from '@/fields/SelectField.vue';
import RadioField from '@/fields/RadioField.vue';
import DateFieldWithNow from '@/fields/DateFieldWithNow.vue';
import MKBFieldForm from '@/fields/MKBFieldForm.vue';
import MKBFieldTreeselect from '@/fields/MKBFieldTreeselect.vue';
import SearchFieldValueField from '@/fields/SearchFieldValueField.vue';

const DEFAULT_SETTINGS = () => ({
  type: 0,
  lines: 1,
  variants: '',
  width: '',
  validator: '',
});

export default {
  name: 'TableField',
  components: {
    DateFieldWithNow,
    RadioField,
    SelectField,
    MKBFieldForm,
    SearchFieldValueField,
    MKBFieldTreeselect,
  },
  props: {
    value: {
      required: false,
    },
    variants: {
      required: true,
    },
    fieldPk: {
      required: true,
    },
    fields: {
      required: true,
    },
    disabled: {
      required: false,
      default: false,
      type: Boolean,
    },
    card_pk: Number,
    iss_pk: Number,
  },
  mounted() {
    this.checkTable();
  },
  beforeDestroy() {
    this.hasErrors = false;
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
      validators: {},
      errors: {},
      errorsCounter: 0,
      hasErrors: false,
    };
  },
  computed: {
    result() {
      return {
        columns: {
          titles: this.params.columns.titles,
          settings: this.settings.map(s => _.pick(s, ['type', 'width'])),
        },
        rows: this.rows,
      };
    },
    otherValues() {
      return this.fields.reduce((a, b) => ({ ...a, [b.pk]: b.value }), {});
    },
    settings() {
      return this.params.columns.settings || [];
    },
  },
  watch: {
    result: {
      deep: true,
      handler() {
        this.validateOnlyRowsValuesDebounced(true);
        this.changeValue(JSON.stringify(this.result));
      },
    },
    otherValues: {
      deep: true,
      handler() {
        this.validateRowsValues();
      },
    },
    rows: {
      deep: true,
      handler() {
        this.validateOnlyRowsValuesDebounced();
      },
    },
    errors: {
      deep: true,
      handler() {
        this.errorsCounter += 1;
      },
    },
    hasErrors: {
      immediate: true,
      handler() {
        this.$root.$emit('table-field:errors:set', this.fieldPk, this.hasErrors);
      },
    },
  },
  model: {
    event: 'modified',
  },
  methods: {
    changeCell(j, i, v) {
      this.rows[j][i] = v;
      this.rows = [...this.rows];
    },
    changeValue(newVal) {
      this.$emit('modified', newVal);
      setTimeout(() => {
        this.validateOnlyRowsValuesDebounced();
      }, 10);
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

      const validators = {};

      for (let i = 0; i < params.columns.settings.length; i++) {
        const s = params.columns.settings[i];
        params.columns.settings[i] = { ...DEFAULT_SETTINGS(), ...s };
        const validatorSource = params.columns.settings[i].validator;

        if (!this.disabled && validatorSource && typeof validatorSource === 'string') {
          try {
            // eslint-disable-next-line no-new-func
            validators[i] = new Function(
              'currentRowN',
              'currentColumnN',
              'currentFieldId',
              'getCellContent',
              'getFieldText',
              validatorSource,
            );
          } catch (error) {
            console.error(error);
            this.$root.$emit('msg', 'error', `Некорректная функция валидации в колонке ${i + 1} поля ${this.fieldPk}`);
          }
        }
      }

      value.rows = value.rows.filter(r => Array.isArray(r) && r.every(v => _.isString(v)));

      this.params = params;
      this.rows = value.rows;
      this.validators = validators;
      this.errors = {};
      this.hasErrors = false;

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
    getCellContent(row, column, fieldId) {
      const r = row - 1;
      const c = column - 1;

      let rows = null;

      if (fieldId === this.fieldPk) {
        rows = this.rows;
      } else {
        const field = this.fields.find(f => f.pk === fieldId && f.field_type === 27);

        if (field) {
          let value = field.value || '{}';
          try {
            value = JSON.parse(value);
          } catch (e) {
            value = {};
          }

          if (Array.isArray(value.rows)) {
            rows = value.rows;
          }
        }
      }

      if (rows && rows.length > r) {
        if (rows[r].length > c) {
          return rows[r][c];
        }
      }

      return null;
    },
    getFieldText(fieldId) {
      return this.otherValues[fieldId] || null;
    },
    callValidator(column, ...args) {
      if (this.validators[column]) {
        return this.validators[column](...args);
      }

      return false;
    },
    validateOnlyRowsValuesDebounced: debounce(function () {
      this.validateRowsValues(true);
    }, 10),
    validateRowsValues(onlyValidator = false) {
      let hasInvalid = false;

      for (let i = 0; i < this.settings.length; i++) {
        const t = this.settings[i].type;

        if (!onlyValidator) {
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

        if (t !== 'rowNumber') {
          for (let j = 0; j < this.rows.length; j++) {
            const validateResult = this.callValidator(i, j + 1, i + 1, this.fieldPk, this.getCellContent, this.getFieldText);
            const cellId = `${this.fieldPk}_${j}_${i}`;

            this.errors[cellId] = validateResult;

            if (validateResult) {
              hasInvalid = true;
            }
          }
        }
      }
      this.errors = { ...this.errors };
      this.errorsCounter += 1;
      this.hasErrors = hasInvalid;
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
