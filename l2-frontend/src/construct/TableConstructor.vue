<template>
  <div style="max-width: 1024px;margin-top: 10px">
    <div class="input-group" style="margin-bottom: 10px">
      <span class="input-group-addon">Число колонок</span>
      <input type="number" class="form-control" v-model.number="columns.count"
             min="1" max="8" placeholder="Название колонки">
    </div>

    <table class="table table-bordered table-condensed" style="table-layout: fixed;"
           v-if="columns.settings && columns.settings.length === columns.count">
      <colgroup>
        <col width="36">
        <col v-for="(_, i) in columns.titles" :width="columns.settings[i] && columns.settings[i].width" :key="i">
      </colgroup>
      <thead>
      <tr>
        <td></td>
        <td v-for="(_, i) in columns.titles" class="cl-td" :key="i">
          <input type="text" class="form-control" v-model="columns.titles[i]">
        </td>
      </tr>
      </thead>
      <tbody>
      <tr v-for="(r, j) in rows" :key="j">
        <td class="cl-td">
          <button class="btn btn-blue-nb nbr" @click="deleteRow(j)" title="Удалить строку" v-tippy>
            <i class="fa fa-times"></i>
          </button>
        </td>
        <td v-for="(_, i) in columns.titles" class="cl-td" :key="i">
          <template v-if="columns.settings[i].type === 0">
            <textarea :rows="columns.settings[i].lines" class="form-control"
                      v-if="columns.settings[i].lines > 1" v-model="r[i]"
                      placeholder="Значение по умолчанию"></textarea>
            <input class="form-control" v-else v-model="r[i]" placeholder="Значение по умолчанию"/>
          </template>
          <div v-else-if="columns.settings[i].type === 1" style="padding: 5px">
            Тип поля дата
          </div>
          <SelectField :variants="columns.settings[i].variants" class="form-control fw"
                       v-else-if="columns.settings[i].type === 10" v-model="r[i]"/>
          <RadioField :variants="columns.settings[i].variants"
                      v-else-if="columns.settings[i].type === 12" v-model="r[i]"/>
          <input class="form-control" v-else-if="columns.settings[i].type === 18" v-model="r[i]" type="number"
                 placeholder="Значение по умолчанию"/>
          <div v-else-if="columns.settings[i].type === 'rowNumber'" style="padding: 5px;">
            <strong>{{r[i]}}</strong>
          </div>
        </td>
      </tr>
      <tr>
        <td :colspan="columns.count + 1">
          <button class="btn btn-blue-nb" @click="addRow">добавить строку</button>
        </td>
      </tr>
      </tbody>
    </table>

    <div>
      <strong>Настройка колонок:</strong>

      <!-- eslint-disable-next-line vue/no-use-v-if-with-v-for -->
      <div v-for="(s, i) in columns.settings" v-if="columns.settings && columns.settings.length === columns.count" :key="i"
           class="column-card card card-1 card-no-hover">
        <strong>Колонка №{{ i + 1 }} {{ columns.titles[i] }}:</strong>
        <div class="input-group" style="margin-bottom: 10px">
          <span class="input-group-addon">Ширина (пиксели или проценты), пример: 42 или 10% или пусто</span>
          <input type="text" class="form-control"
                 v-model.trim="columns.settings[i].width" @change="updatedSettings" placeholder="Ширина">
        </div>
        <div class="input-group" style="margin-bottom: 10px">
          <span class="input-group-addon">Тип</span>
          <select class="form-control" v-model="columns.settings[i].type" @change="updatedSettings">
            <option :value="t[0]" v-for="t in COLUMN_TYPES" :key="t[0]">{{ t[1] }}</option>
          </select>
        </div>
        <div class="input-group" style="margin-bottom: 10px"
             v-if="columns.settings[i].type === 0">
          <span class="input-group-addon">Число строк в тексте</span>
          <input type="number" class="form-control"
                 v-model.number="columns.settings[i].lines" @change="updatedSettings"
                 min="1" max="12" placeholder="Число строк в тексте">
        </div>
        <div class="input-group" style="margin-bottom: 10px"
             v-if="[10, 12].includes(columns.settings[i].type)">
          <span class="input-group-addon">Варианты (по строкам)</span>
          <textarea class="form-control" v-model="columns.settings[i].variants"
                    @change="updatedSettings"
                    v-autosize="columns.settings[i].variants"></textarea>
        </div>
      </div>
    </div>

    <label>
      <input type="checkbox" v-model="dynamicRows"/> пользователь может менять число строк
    </label>
  </div>
</template>
<script>
import _ from 'lodash';
import SelectField from '@/fields/SelectField.vue';
import RadioField from '@/fields/RadioField.vue';

const DEFAULT_TITLES = [
  'Колонка 1',
  'Колонка 2',
];

const DEFAULT_ROWS = [
  [
    '',
    '',
  ],
];

const COLUMN_TYPES = [
  [0, 'Текст'],
  [1, 'Дата'],
  [10, 'Справочник'],
  [12, 'Радио'],
  [18, 'Число'],
  ['rowNumber', 'Номер строки'],
];

const DEFAULT_SETTINGS = () => ({
  type: 0,
  lines: 1,
  variants: '',
  width: '',
});

export default {
  name: 'TableConstructor',
  components: { RadioField, SelectField },
  props: {
    row: {},
  },
  mounted() {
    this.checkTable();
  },
  data() {
    return {
      columns: {
        count: 2,
        titles: DEFAULT_TITLES,
        settings: [],
      },
      rows: DEFAULT_ROWS,
      dynamicRows: true,
      COLUMN_TYPES,
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

      if (!Array.isArray(params.columns.settings)) {
        params.columns.settings = [];
      }

      if (!Array.isArray(params.columns.titles)) {
        params.columns.titles = DEFAULT_TITLES;
      }

      if (!Array.isArray(params.rows)) {
        params.rows = DEFAULT_ROWS;
      }

      params.rows = params.rows.filter((r) => Array.isArray(r) && r.every((v) => _.isString(v)));

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
      this.validateSettings();
    },
    updatedSettings() {
      this.validateSettings();
    },
    validateSettings() {
      const c = this.columns.count;
      this.columns.settings = _.cloneDeep(this.columns.settings || []);
      if (this.columns.settings.length < c) {
        const needToAdd = c - this.columns.settings.length;
        for (let i = 0; i < needToAdd; i++) {
          this.columns.settings.push({});
        }
      } else if (this.columns.settings.length > c) {
        this.columns.settings.splice(c);
      }

      for (let i = 0; i < this.columns.settings.length; i++) {
        let s = this.columns.settings[i];
        if (!_.isObject(s)) {
          s = {};
        }
        this.columns.settings[i] = { ...DEFAULT_SETTINGS(), ...s };
        if (!this.COLUMN_TYPES.map((t) => t[0]).includes(this.columns.settings[i].type)) {
          // eslint-disable-next-line prefer-destructuring
          this.columns.settings[i].type = this.COLUMN_TYPES[0][0];
        }

        const t = this.columns.settings[i].type;

        if (t !== 0) {
          for (let j = 0; j < this.rows.length; j++) {
            const r = this.rows[j];
            if (t === 1) {
              r[i] = '';
            } else if (t === 'rowNumber') {
              r[i] = `${j + 1}`;
            } else if (t === 18) {
              if (_.isNaN(Number(r[i]))) {
                r[i] = '';
              }
            }

            if (t === 10 || t === 12) {
              const v = this.columns.settings[i].variants.split('\n');
              if (!v.includes(r[i])) {
                // eslint-disable-next-line prefer-destructuring
                r[i] = v[0];
              }
            } else {
              this.columns.settings[i].variants = '';
            }
          }
        }
      }
    },
    validateColumnsLength() {
      if (this.columns.count > 8) {
        this.columns.count = 8;
      } else if (this.columns.count === 0) {
        this.columns.count = 1;
      }
      const c = this.columns.count;
      if (this.columns.titles.length < c) {
        const needToAdd = c - this.columns.titles.length;
        for (let i = 0; i < needToAdd; i++) {
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
          const needToAdd = c - r.length;
          for (let i = 0; i < needToAdd; i++) {
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
.column-card {
  padding: 5px;
}
</style>
