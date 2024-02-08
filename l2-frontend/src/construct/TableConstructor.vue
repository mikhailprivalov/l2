<template>
  <div style="max-width: 1024px;margin-top: 10px">
    <div
      class="input-group"
      style="margin-bottom: 10px"
    >
      <span class="input-group-addon">Число колонок</span>
      <input
        v-model.number="columns.count"
        type="number"
        class="form-control"
        min="1"
        max="8"
        placeholder="Название колонки"
      >
    </div>

    <table
      v-if="columns.settings && columns.settings.length === columns.count"
      class="table table-bordered table-condensed"
      style="table-layout: fixed;"
    >
      <colgroup>
        <col width="36">
        <col
          v-for="(_, i) in columns.titles"
          :key="i"
          :width="columns.settings[i] && columns.settings[i].width"
        >
      </colgroup>
      <thead>
        <tr>
          <td />
          <td
            v-for="(_, i) in columns.titles"
            :key="i"
            class="cl-td"
          >
            <input
              v-model="columns.titles[i]"
              type="text"
              class="form-control"
            >
          </td>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(r, j) in rows"
          :key="j"
        >
          <td class="cl-td">
            <button
              v-tippy
              class="btn btn-blue-nb nbr"
              title="Удалить строку"
              @click="deleteRow(j)"
            >
              <i class="fas fa-times" />
            </button>
          </td>
          <td
            v-for="(_, i) in columns.titles"
            :key="i"
            class="cl-td"
            :class="columns.settings[i].type === 2 && 'mkb'"
          >
            <template v-if="columns.settings[i].type === 0">
              <textarea
                v-if="columns.settings[i].lines > 1"
                v-model="r[i]"
                :rows="columns.settings[i].lines"
                class="form-control"
                placeholder="Значение по умолчанию"
              />
              <input
                v-else
                v-model="r[i]"
                class="form-control"
                placeholder="Значение по умолчанию"
              >
            </template>
            <div
              v-else-if="columns.settings[i].type === 1"
              style="padding: 5px"
            >
              Тип поля дата
            </div>
            <SelectField
              v-else-if="columns.settings[i].type === 10"
              v-model="r[i]"
              :variants="columns.settings[i].variants"
              class="form-control fw"
            />
            <RadioField
              v-else-if="columns.settings[i].type === 12"
              v-model="r[i]"
              :variants="columns.settings[i].variants"
            />
            <input
              v-else-if="columns.settings[i].type === 18"
              v-model="r[i]"
              class="form-control"
              type="number"
              placeholder="Значение по умолчанию"
            >
            <MKBFieldForm
              v-else-if="columns.settings[i].type === 2"
              v-model="r[i]"
              :short="false"
            />
            <input
              v-else-if="[23].includes(columns.settings[i].type)"
              v-model="r[i]"
              class="form-control"
              placeholder="Ссылка на значение"
            >
            <input
              v-else-if="[32, 33, 34, 36].includes(columns.settings[i].type)"
              v-model="r[i]"
              class="form-control"
              placeholder="Ссылка на поле (%)"
            >
            <div
              v-else-if="columns.settings[i].type === 'rowNumber'"
              style="padding: 5px;"
            >
              <strong>{{ r[i] }}</strong>
            </div>
          </td>
        </tr>
        <tr>
          <td :colspan="columns.count + 1">
            <button
              class="btn btn-blue-nb"
              @click="addRow"
            >
              добавить строку
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="columns.settings && columns.settings.length === columns.count">
      <strong>Настройка колонок:</strong>

      <div
        v-for="(s, i) in columns.settings"
        :key="i"
        class="column-card card card-1 card-no-hover"
      >
        <strong>Колонка №{{ i + 1 }} {{ columns.titles[i] }}:</strong>
        <div
          class="input-group"
          style="margin-bottom: 10px"
        >
          <span class="input-group-addon">Ширина (пиксели или проценты), пример: 42 или 10% или пусто</span>
          <input
            v-model.trim="columns.settings[i].width"
            type="text"
            class="form-control"
            placeholder="Ширина"
            @change="updatedSettings"
          >
        </div>
        <div
          class="input-group"
          style="margin-bottom: 10px"
        >
          <span class="input-group-addon">Тип</span>
          <select
            v-model="columns.settings[i].type"
            class="form-control"
            @change="updatedSettings"
          >
            <option
              v-for="t in COLUMN_TYPES"
              :key="t[0]"
              :value="t[0]"
            >
              {{ t[1] }}
            </option>
          </select>
        </div>
        <div
          v-if="columns.settings[i].type === 0"
          class="input-group"
          style="margin-bottom: 10px"
        >
          <span class="input-group-addon">Число строк в тексте</span>
          <input
            v-model.number="columns.settings[i].lines"
            type="number"
            class="form-control"
            min="1"
            max="12"
            placeholder="Число строк в тексте"
            @change="updatedSettings"
          >
        </div>
        <div
          v-if="[10, 12].includes(columns.settings[i].type)"
          class="input-group"
          style="margin-bottom: 10px"
        >
          <span class="input-group-addon">Варианты (по строкам)</span>
          <textarea
            v-model="columns.settings[i].variants"
            v-autosize="columns.settings[i].variants"
            class="form-control"
            @change="updatedSettings"
          />
        </div>
        <div
          v-if="columns.settings[i].type === 'relatedMultiselect'"
          style="margin-bottom: 10px"
        >
          <div
            class="input-group"
            style="margin-bottom: 10px"
          >
            <span class="input-group-addon">Связанная колонка</span>
            <select
              v-model="columns.settings[i].linked"
              class="form-control"
              @change="updatedSettings"
            >
              <option :value="null">
                - не выбрано
              </option>
              <option
                v-for="(_, j) in columns.settings"
                v-if="/* eslint-disable-line vue/no-use-v-if-with-v-for */ j !== i"
                :key="j"
                :value="j"
              >
                {{ columns.titles[j] }}
              </option>
            </select>
          </div>
          <TableMultiselectEditor
            v-model="columns.settings[i].multiVariants"
            :linked-variants="getVariantsOfLinked(i)"
            @change="updatedSettings"
          />
        </div>
        <v-collapse-wrapper v-if="columns.settings[i].type !== 'rowNumber'">
          <div
            v-collapse-toggle
            class="header"
          >
            <a
              href="#"
              class="a-under"
              @click.prevent
            >
              Проверка корректности ячеек колонки
            </a>
          </div>
          <div
            v-collapse-content
            class="code-editor"
          >
            <div class="code-help">
              Код ниже является телом функции-валидатора.<br>
              Сделайте <code>return false;</code>, если значение корректно.<br>
              Если значение некорректно, то верните сообщение об ошибке.<br>
              Например <code>return "Ячейка не может быть пуста";</code>
              <div>
                <strong>
                  Доступные параметры и функции
                </strong>
                <ul>
                  <li><code>currentRowN</code> – текущая строка (начинается с 1)</li>
                  <li><code>currentColumnN</code> – текущая колонка (начинается с 1)</li>
                  <li><code>currentFieldId</code> – id текущего поля</li>
                  <li><code>getCellContent(rowN, columnN, fieldId)</code> – получение значения ячейки из таблицы поля</li>
                  <li><code>getFieldText(fieldId)</code> – получение текстового значения поля</li>
                  <li>
                    <code>getCellContent</code> и <code>getFieldText</code> – вернёт null, если поле или строка или ячейка не
                    найдены
                  </li>
                </ul>
              </div>
            </div>
            <VueCodeditor
              v-model.lazy="columns.settings[i].validator"
              mode="javascript"
              theme="cobalt"
              @input="updateValidator(i, $event)"
            />
          </div>
        </v-collapse-wrapper>
      </div>
    </div>

    <label> <input
      v-model="dynamicRows"
      type="checkbox"
    > пользователь может менять число строк </label>
  </div>
</template>

<script lang="ts">
import _ from 'lodash';
import { debounce } from 'lodash/function';
import VueCodeditor from 'vue-codeditor';

import SelectField from '@/fields/SelectField.vue';
import RadioField from '@/fields/RadioField.vue';
import MKBFieldForm from '@/fields/MKBFieldForm.vue';
import TableMultiselectEditor from '@/construct/TableMutiselectEditor.vue';

const DEFAULT_TITLES = ['Колонка 1', 'Колонка 2'];

const DEFAULT_ROWS = [['', '']];

const COLUMN_TYPES = [
  [0, 'Текст'],
  [1, 'Дата'],
  [10, 'Справочник'],
  [12, 'Радио'],
  [18, 'Число'],
  ['rowNumber', 'Номер строки'],
  [2, 'Диагноз по МКБ'],
  [32, 'МКБ-внешние причины'],
  [33, 'МКБ-алфавитный'],
  [34, 'МКБ-обычный'],
  [36, 'МКБ-комбинация (1489, 692)'],
  [23, 'Ссылка на значение'],
  [35, 'Врач'],
  ['relatedMultiselect', 'Зависимый множественный выбор'],
];

const DEFAULT_SETTINGS = () => ({
  type: 0,
  lines: 1,
  variants: '',
  multiVariants: [],
  linked: null,
  width: '',
  validator: '',
});

export default {
  name: 'TableConstructor',
  components: {
    RadioField,
    SelectField,
    MKBFieldForm,
    VueCodeditor,
    TableMultiselectEditor,
  },
  props: {
    row: {},
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
        this.updateValue();
      },
    },
  },
  mounted() {
    this.checkTable();
  },
  methods: {
    getVariantsOfLinked(i) {
      const linkedIndex = this.columns.settings[i].linked;

      if (linkedIndex === null) {
        return '';
      }

      const linked = this.columns.settings[linkedIndex];

      if (linked.type !== 10 && linked.type !== 12) {
        return '';
      }

      return linked.variants;
    },
    updateValidator: debounce(function (i, v) {
      this.columns.settings[i].validator = v;
      this.updateValue();
    }, 100),
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

      params.columns = params.columns || this.columns;
      params.rows = params.rows || this.rows;
      params.dynamicRows = Boolean(Object.keys(params).includes('dynamicRows') ? params.dynamicRows : this.dynamicRows);

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

      params.rows = params.rows.filter(r => Array.isArray(r) && r.every(v => _.isString(v)));

      if (params.rows.length === 0) {
        params.rows = DEFAULT_ROWS;
      }

      this.columns = params.columns;
      this.rows = params.rows;
      this.dynamicRows = params.dynamicRows;

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

        if (typeof this.columns.settings[i].validator !== 'string') {
          this.columns.settings[i].validator = '';
        }

        if (!this.COLUMN_TYPES.map(t => t[0]).includes(this.columns.settings[i].type)) {
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
            } else if (t !== 'relatedMultiselect') {
              this.columns.settings[i].variants = '';
              this.columns.settings[i].multiVariants = [];
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

.code-editor ::v-deep {
  .ace_editor {
    min-height: 100px;
  }

  .ace_editor,
  .ace_editor * {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Droid Sans Mono', 'Consolas', monospace !important;
    font-size: 12px !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
  }
}

.code-help {
  margin-bottom: 10px;
  padding: 10px;
  background-color: rgba(0, 0, 0, 8%);
  border-radius: 4px;
}
</style>
