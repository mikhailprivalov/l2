<template>
  <div class="root">
    <div class="top-editor" :class="{simpleEditor: simple, formEditor: ex_dep === 12}">
      <div class="left">
        <div class="input-group">
          <span class="input-group-addon" v-if="ex_dep === 12">
            Название шаблона параметров направления ({{ loaded_pk }})
          </span>
          <span class="input-group-addon" v-else>Полное наименование</span>
          <input type="text" class="form-control" v-model="title">
          <label v-if="ex_dep === 12" class="input-group-addon" style="height: 34px;text-align: left;">
            <input type="checkbox" v-model="is_global_direction_params"/> Глобальный
          </label>
          <span class="input-group-btn" v-if="(ex_dep === 12 || simple) && fte">
            <button class="btn btn-blue-nb"
                    type="button"
                    style="border-radius: 0;width: 100%;"
                    :disabled="has_unsaved || loaded_pk < 0"
                    @click="f_templates()">
              Шаблоны быстрого ввода
            </button>
          </span>
        </div>
        <div class="input-group" v-if="ex_dep !== 12">
          <span class="input-group-addon">Краткое <small>(для создания направлений)</small></span>
          <input type="text" class="form-control" v-model="short_title">
          <span class="input-group-addon">Профиль</span>
          <select class="form-control" v-model="speciality">
            <option :value="d.pk" :key="d.pk" v-for="d in specialities">
              {{ d.title }}
            </option>
          </select>
        </div>
      </div>
      <div class="right" v-if="!simple && ex_dep !== 12">
        <div class="row" style="margin-right: 0;" v-if="department < -1">
          <div class="col-xs-6" style="padding-right: 0">
            <div class="input-group" style="margin-right: -1px">
              <span class="input-group-addon">Код (ОМС)</span>
              <input type="text" class="form-control f-code" v-model="code">
              <span class="input-group-addon">Код (внутр)</span>
              <input type="text" class="form-control f-code" v-model="internal_code">
            </div>
          </div>
          <div class="col-xs-6" style="padding-left: 0;padding-right: 0;margin-right: 0;">
            <div class="input-group">
              <span class="input-group-addon">Подраздел</span>
              <select v-model="site_type" class="form-control">
                <option v-for="r in ex_deps" :value="r.pk" :key="r.pk">{{ r.title }}</option>
              </select>
            </div>
          </div>
        </div>
        <div class="input-group" v-else>
          <span class="input-group-addon">Код (ОМС)</span>
          <input type="text" class="form-control f-code" v-model="code">
          <span class="input-group-addon">Код (внутр)</span>
          <input type="text" class="form-control f-code" v-model="internal_code">
        </div>
        <div class="input-group">
          <span class="input-group-addon"> Ф.направления </span>
          <select class="form-control" v-model="direction_current_form">
            <option :value="d[0]" v-for="d in direction_forms" :key="d[0]">
              {{ d[1] }}
            </option>
          </select>
          <label class="input-group-addon" style="height: 34px;text-align: left;">
            <input type="checkbox" v-model="hide"/> Скрытие исследования
          </label>
          <span class="input-group-btn" v-if="fte">
            <button class="btn btn-blue-nb"
                    type="button"
                    style="border-radius: 0;width: 100%;"
                    :disabled="has_unsaved || loaded_pk < 0"
                    @click="f_templates()">
              Шаблоны быстрого ввода
            </button>
          </span>
        </div>
      </div>
    </div>
    <div class="content-editor">
      <template v-if="ex_dep !== 12">
        <div class="input-group" v-if="!simple">
          <span class="input-group-addon nbr">Информация на направлении</span>
          <textarea class="form-control noresize" v-autosize="info" v-model="info"></textarea>
        </div>
        <div class="input-group" v-if="direction_params_all.length > 1">
          <span class="input-group-addon nbr" style="width: 233px">Параметры для направления</span>
          <treeselect class="treeselect-noborder treeselect-wide"
                      :multiple="false" :disable-branch-nodes="true"
                      :options="direction_params_all"
                      placeholder="Параметр не выбран" v-model="direction_current_params"
                      :append-to-body="true"
                      :clearable="false"
          />
        </div>
      </template>
      <div v-if="ex_dep === 7" class="department-select">
        <treeselect :multiple="false" :disable-branch-nodes="true" :options="departments"
                    placeholder="Отделение не выбрано" v-model="hospital_research_department_pk"/>
      </div>
      <template v-if="ex_dep !== 7">
        <div v-for="(group, gi) in orderBy(groups, 'order')" :key="gi" class="ed-group">
          <div class="input-group" v-if="ex_dep !== 12">
            <span class="input-group-btn">
              <button class="btn btn-blue-nb lob" :disabled="is_first_group(group)" @click="dec_group_order(group)">
                <i class="glyphicon glyphicon-arrow-up"></i>
              </button>
            </span>
            <span class="input-group-btn">
              <button class="btn btn-blue-nb nob" :disabled="is_last_group(group)" @click="inc_group_order(group)">
                <i class="glyphicon glyphicon-arrow-down"></i>
              </button>
            </span>
            <span class="input-group-addon">Название группы ({{ group.pk === -1 ? 'новое' : group.pk }})</span>
            <input type="text" class="form-control" placeholder="Название" v-model="group.title">
            <span class="input-group-addon">Условие видимости</span>
            <input type="text" class="form-control" placeholder="Условие" v-model="group.visibility">
          </div>
          <div class="row" v-if="ex_dep !== 12">
            <div class="col-xs-6">
              <label v-if="!group.hide">Отображать название <input type="checkbox" v-model="group.show_title"/></label>
              <div v-else>
                <strong>Группа скрыта.</strong>
                <label><input type="checkbox" v-model="group.display_hidden"/> отображать поля</label>
              </div>
            </div>
            <div class="col-xs-6 text-right">
              <label>Скрыть группу <input type="checkbox" v-model="group.hide"/></label>
            </div>
          </div>
          <template v-if="!group.hide || group.display_hidden">
            <div>
              <strong>Поля ввода</strong>
            </div>
            <div v-for="(row, ri) in orderBy(group.fields, 'order')" :key="ri" class="ed-field">
              <div class="ed-field-inner">
                <div>
                  <button class="btn btn-default btn-sm btn-block" :disabled="is_first_field(group, row)"
                          @click="dec_order(group, row)">
                    <i class="glyphicon glyphicon-arrow-up"></i>
                  </button>
                  <button class="btn btn-default btn-sm btn-block" :disabled="is_last_field(group, row)"
                          @click="inc_order(group, row)">
                    <i class="glyphicon glyphicon-arrow-down"></i>
                  </button>
                </div>
                <div>
                  <div class="input-group">
                    <span class="input-group-addon">Название поля ({{ row.pk === -1 ? 'новое' : row.pk }})</span>
                    <input type="text" class="form-control" v-model="row.title">
                    <span class="input-group-addon">ID-скрепки</span>
                    <input type="text" class="form-control" v-model="row.attached">
                  </div>
                  <div v-if="row.field_type === 0">
                    <strong>Значение по умолчанию:</strong>
                    <textarea v-model="row.default" :rows="row.lines" class="form-control"
                              v-if="row.lines > 1"></textarea>
                    <input v-model="row.default" class="form-control" v-else/>
                  </div>
                  <div v-else-if="row.field_type === 3">
                    <strong>Формула:</strong>
                    <input v-model="row.default" class="form-control"/>
                  </div>
                  <div v-else-if="row.field_type === 11">
                    <strong>ID фракции:</strong>
                    <input v-model="row.default" class="form-control"/>
                  </div>
                  <div v-else-if="row.field_type === 13 || row.field_type === 14 || row.field_type === 23">
                    <strong>ID поля:</strong>
                    <input v-model="row.default" class="form-control"/>
                  </div>
                  <div v-else-if="row.field_type === 15">
                    <strong>Значение по умолчанию:</strong>
                    <rich-text-editor v-model="row.default"/>
                  </div>
                  <div v-else-if="row.field_type === 18">
                    <strong>Значение по умолчанию:</strong>
                    <NumberField v-model="row.default"/>
                  </div>
                  <div v-else-if="row.field_type === 19">
                    <strong>Значение по умолчанию:</strong>
                    <NumberRangeField :variants="row.values_to_input" v-model="row.default"/>
                  </div>
                  <div v-else-if="row.field_type === 21">
                    <ConfigureAnesthesiaField v-model="row.values_to_input"/>
                  </div>
                  <div v-else-if="row.field_type === 24">
                    <strong>Результаты лабораторные:</strong>
                  </div>
                  <div v-else-if="row.field_type === 25">
                    <strong>Результаты диагностические:</strong>
                  </div>
                  <div v-else-if="row.field_type === 26">
                    <strong>Результаты консультационные:</strong>
                  </div>
                  <div v-else-if="row.field_type === 27">
                    <strong>Таблица:</strong>
                  </div>
                  <v-collapse-wrapper v-show="[0, 10, 12, 13, 14, 19, 22, 23, 27].includes(row.field_type)">
                    <div class="header" v-collapse-toggle>
                      <a href="#" class="a-under" @click.prevent v-if="row.field_type === 0">
                        Шаблоны быстрого ввода (кол-во: {{ row.values_to_input.length }})
                      </a>
                      <a href="#" class="a-under" @click.prevent v-else-if="row.field_type === 19">
                        Мин, Макс, Шаг, Единицы измерения
                      </a>
                      <a href="#" class="a-under" @click.prevent v-else-if="row.field_type === 27">
                        Настройка таблицы
                      </a>
                      <a href="#" class="a-under" @click.prevent v-else>
                        Варианты (кол-во: {{ row.values_to_input.length }})
                      </a>
                    </div>
                    <div class="my-content" v-collapse-content>
                      <TableConstructor :row="row" v-if="row.field_type === 27"/>
                      <template v-else>
                        <div class="input-group" style="margin-bottom: 5px">
                          <input type="text" v-model="row.new_value" class="form-control"
                                 @keyup.enter="add_template_value(row)"
                                 placeholder="Новый шаблон быстрого ввода"/>
                          <span class="input-group-btn"><button class="btn last btn-blue-nb" type="button"
                                                                :disabled="row.new_value === ''"
                                                                @click="add_template_value(row)">Добавить</button></span>
                        </div>
                        <div>
                          <div class="input-group" v-for="(v, i) in row.values_to_input" :key="i"
                               style="margin-bottom: 1px">
                            <span class="input-group-btn">
                              <button class="btn btn-blue-nb lob" :disabled="is_first_in_template(i)"
                                      @click="up_template(row, i)">
                                <i class="glyphicon glyphicon-arrow-up"></i>
                              </button>
                              </span>
                            <span class="input-group-btn">
                              <button class="btn btn-blue-nb nob" :disabled="is_last_in_template(row, i)"
                                      @click="down_template(row, i)">
                                <i class="glyphicon glyphicon-arrow-down"></i>
                              </button>
                            </span>
                            <input class="form-control" type="text" v-model="row.values_to_input[i]"/>
                            <span class="input-group-btn">
                              <button class="btn btn-blue-nb" @click="remove_template(row, i)">
                                <i class="glyphicon glyphicon-remove"></i>
                              </button>
                            </span>
                          </div>
                        </div>
                      </template>
                    </div>
                  </v-collapse-wrapper>
                  <FieldHelper :fieldType="row.field_type" :value="row.default" :groups="groups"/>
                </div>
                <div>
                  <strong>Подсказка:</strong>
                  <textarea class="form-control" v-model="row.helper"></textarea>
                </div>
                <div>
                  <strong>Условие видимости:</strong>
                  <textarea class="form-control" v-model="row.visibility"></textarea>
                </div>
                <div>
                  <label>
                    <input type="checkbox" v-model="row.hide"/> скрыть поле
                  </label>
                  <label>
                    <input type="checkbox" v-model="row.required"/> запрет пустого
                  </label>
                  <label>
                    <input type="checkbox" v-model="row.for_talon"/> в талон
                  </label>
                  <label>
                    <input type="checkbox" v-model="row.for_extract_card"/> в выписку
                  </label>
                  <label>
                    <input type="checkbox" v-model="row.for_med_certificate"/> в справку
                  </label>
                  <label style="line-height: 1"
                         v-show="row.field_type === 0 || row.field_type === 13 || row.field_type === 14 || row.field_type === 23">
                    Число строк:<br/>
                    <input class="form-control" type="number" min="1" v-model.number="row.lines"/>
                  </label>
                  <label>
                    Тип поля:<br/>
                    <select v-model.number="row.field_type" class="form-control">
                      <option value="0">Строка</option>
                      <option value="1">Дата</option>
                      <option value="2">Диагноз по МКБ</option>
                      <option value="3">Расчётное</option>
                      <option value="10">Справочник</option>
                      <option value="11">Фракция</option>
                      <option value="12">Радио</option>
                      <option value="13">Поле описательного результата</option>
                      <option value="14">Поле описательного результата без заголовка</option>
                      <option value="15">Текст с форматированием</option>
                      <option value="16">(Стационар) агрегация по лаборатории</option>
                      <option value="17">(Стационар) агрегация по описательным</option>
                      <option value="18">Число</option>
                      <option value="19">Число через range</option>
                      <option value="20">Время ЧЧ:ММ</option>
                      <option value="21">Течение анестезии (таблица)</option>
                      <option value="22">Текст с автозаполнением</option>
                      <option value="23">Ссылка без автозагрузки</option>
                      <option value="24">Результаты лабораторные</option>
                      <option value="25">Результаты диагностические</option>
                      <option value="26">Результаты консультаций</option>
                      <option value="27">Таблица</option>
                    </select>
                  </label>
                </div>
              </div>
            </div>
            <div>
              <button class="btn btn-blue-nb" @click="add_field(group)">Добавить поле</button>
            </div>
          </template>
        </div>
        <div v-if="ex_dep !== 12">
          <button class="btn btn-blue-nb" @click="add_group">Добавить группу</button>
        </div>
      </template>
      <div v-if="ex_dep === 12 && pk > -1">
        <div><strong>Назначения, где используется этот шаблон параметров:</strong></div>
        <ul>
          <li v-for="a in assigned_to_params" :key="a">{{ a }}</li>
          <li v-if="assigned_to_params.length === 0">не найдено</li>
        </ul>
      </div>
    </div>
    <div class="footer-editor">
      <button class="btn btn-blue-nb" @click="cancel">Отмена</button>
      <button class="btn btn-blue-nb" :disabled="!valid" @click="save">Сохранить</button>
    </div>
    <fast-templates-editor v-if="f_templates_open"
                           :title="title"
                           :research_pk="loaded_pk"
                           :groups="groups"
    />
  </div>
</template>

<script>
import Vue from 'vue';
import Vue2Filters from 'vue2-filters';

import construct_point from '@/api/construct-point';
import * as actions from '@/store/action-types';
import NumberRangeField from '@/fields/NumberRangeField.vue';
import ConfigureAnesthesiaField from '@/fields/ConfigureAnesthesiaField.vue';
import RichTextEditor from '@/fields/RichTextEditor.vue';
import NumberField from '@/fields/NumberField.vue';
import FieldHelper from '@/ui-cards/FieldHelper.vue';

import api from '@/api';

import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import TableConstructor from '@/construct/TableConstructor.vue';
import FastTemplatesEditor from './FastTemplatesEditor.vue';

Vue.use(Vue2Filters);

export default {
  name: 'paraclinic-research-editor',
  components: {
    TableConstructor,
    FieldHelper,
    NumberRangeField,
    NumberField,
    RichTextEditor,
    FastTemplatesEditor,
    ConfigureAnesthesiaField,
    Treeselect,
  },
  mixins: [Vue2Filters.mixin],
  props: {
    pk: {
      type: Number,
      required: true,
    },
    department: {
      type: Number,
      required: true,
    },
    simple: {
      type: Boolean,
      required: false,
      default: false,
    },
    main_service_pk: {
      type: Number,
      required: false,
      default: -1,
    },
    hs_pk: {
      type: Number,
      required: false,
      default: -1,
    },
    hide_main: {
      type: Boolean,
      required: false,
      default: false,
    },
    direction_forms: {
      type: Array,
      required: false,
      default: () => [],
    },
    specialities: {
      type: Array,
      required: false,
      default: () => [],

    },
  },
  created() {
    this.load();
    this.load_deparments();
  },
  data() {
    return {
      title: '',
      short_title: '',
      is_global_direction_params: false,
      code: '',
      internal_code: '',
      direction_current_form: '',
      info: '',
      hide: false,
      cancel_do: false,
      loaded_pk: -2,
      site_type: null,
      groups: [],
      template_add_types: [
        { sep: ' ', title: 'Пробел' },
        { sep: ', ', title: 'Запятая и пробел' },
        { sep: '; ', title: 'Точка с запятой (;) и пробел' },
        { sep: '. ', title: 'Точка и пробел' },
        { sep: '\n', title: 'Перенос строки' },
      ],
      has_unsaved: false,
      f_templates_open: false,
      templates: [],
      opened_template_data: {},
      speciality: -1,
      departments: [],
      hospital_research_department_pk: -1,
      direction_params_all: [],
      direction_current_params: -1,
      assigned_to_params: [],
    };
  },
  watch: {
    pk() {
      this.load();
    },
    loaded_pk() {
      this.has_unsaved = false;
    },
    groups: {
      handler(n, o) {
        if (o && o.length > 0) {
          this.has_unsaved = true;
        }
      },
      deep: true,
    },
  },
  mounted() {
    window.$(window).on('beforeunload', () => {
      if (this.has_unsaved && this.loaded_pk > -2 && !this.cancel_do) {
        return 'Изменения, возможно, не сохранены. Вы уверены, что хотите покинуть страницу?';
      }
      return undefined;
    });
    this.$root.$on('hide_fte', () => this.f_templates_hide());
  },
  computed: {
    fte() {
      return this.$store.getters.modules.l2_fast_templates;
    },
    valid() {
      return this.norm_title.length > 0 && !this.cancel_do && (!this.simple || this.main_service_pk !== -1);
    },
    norm_title() {
      return this.title.trim();
    },
    min_max_order_groups() {
      let min = 0;
      let max = 0;
      for (const row of this.groups) {
        if (min === 0) {
          min = row.order;
        } else {
          min = Math.min(min, row.order);
        }
        max = Math.max(max, row.order);
      }
      return { min, max };
    },
    ex_dep() {
      return {
        '-2': 4,
        '-3': 5,
        '-4': 6,
        '-5': 7,
        '-6': 8,
        '-9': 11,
        '-10': 12,
      }[this.department] || this.department;
    },
    ex_deps() {
      return this.$store.getters.ex_dep[this.ex_dep] || [];
    },
  },
  methods: {
    f_templates() {
      this.f_templates_open = true;
    },
    f_templates_hide() {
      this.f_templates_open = false;
    },
    is_first_in_template(i) {
      return i === 0;
    },
    is_last_in_template(row, i) {
      return i === row.values_to_input.length - 1;
    },
    up_template(row, i) {
      if (this.is_first_in_template(i)) return;
      const values = JSON.parse(JSON.stringify(row.values_to_input));
      [values[i - 1], values[i]] = [values[i], values[i - 1]];
      // eslint-disable-next-line no-param-reassign
      row.values_to_input = values;
    },
    down_template(row, i) {
      if (this.is_last_in_template(row, i)) return;
      const values = JSON.parse(JSON.stringify(row.values_to_input));
      [values[i + 1], values[i]] = [values[i], values[i + 1]];
      // eslint-disable-next-line no-param-reassign
      row.values_to_input = values;
    },
    remove_template(row, i) {
      if (row.values_to_input.length - 1 < i) return;
      row.values_to_input.splice(i, 1);
    },
    add_template_value(row) {
      if (row.new_value === '') return;
      row.values_to_input.push(row.new_value);
      // eslint-disable-next-line no-param-reassign
      row.new_value = '';
    },
    drag() {
      // console.log(row, ev)
    },
    min_max_order(group) {
      let min = 0;
      let max = 0;
      for (const row of group.fields) {
        if (min === 0) {
          min = row.order;
        } else {
          min = Math.min(min, row.order);
        }
        max = Math.max(max, row.order);
      }
      return { min, max };
    },
    inc_group_order(row) {
      if (row.order === this.min_max_order_groups.max) return;
      const next_row = this.find_group_by_order(row.order + 1);
      if (next_row) {
        next_row.order--;
      }
      // eslint-disable-next-line no-param-reassign
      row.order++;
    },
    dec_group_order(row) {
      if (row.order === this.min_max_order_groups.min) return;
      const prev_row = this.find_group_by_order(row.order - 1);
      if (prev_row) {
        prev_row.order++;
      }
      // eslint-disable-next-line no-param-reassign
      row.order--;
    },
    inc_order(group, row) {
      if (row.order === this.min_max_order(group).max) return;
      const next_row = this.find_by_order(group, row.order + 1);
      if (next_row) {
        next_row.order--;
      }
      // eslint-disable-next-line no-param-reassign
      row.order++;
    },
    dec_order(group, row) {
      if (row.order === this.min_max_order(group).min) return;
      const prev_row = this.find_by_order(group, row.order - 1);
      if (prev_row) {
        prev_row.order++;
      }
      // eslint-disable-next-line no-param-reassign
      row.order--;
    },
    find_by_order(group, order) {
      for (const row of group.fields) {
        if (row.order === order) {
          return row;
        }
      }
      return false;
    },
    find_group_by_order(order) {
      for (const row of this.groups) {
        if (row.order === order) {
          return row;
        }
      }
      return false;
    },
    is_first_group(group) {
      return group.order === this.min_max_order_groups.min;
    },
    is_last_group(group) {
      return group.order === this.min_max_order_groups.max;
    },
    is_first_field(group, row) {
      return row.order === this.min_max_order(group).min;
    },
    is_last_field(group, row) {
      return row.order === this.min_max_order(group).max;
    },
    add_field(group) {
      let order = 0;
      for (const row of group.fields) {
        order = Math.max(order, row.order);
      }
      group.fields.push({
        pk: -1,
        order: order + 1,
        title: '',
        default: '',
        values_to_input: [],
        new_value: '',
        hide: false,
        lines: 3,
        field_type: 0,
      });
    },
    add_group() {
      let order = 0;
      for (const row of this.groups) {
        order = Math.max(order, row.order);
      }
      const g = {
        pk: -1, order: order + 1, title: '', fields: [], show_title: true, hide: false,
      };
      this.add_field(g);
      this.groups.push(g);
    },
    load() {
      this.title = '';
      this.short_title = '';
      this.is_global_direction_params = false;
      this.code = '';
      this.info = '';
      this.hide = false;
      this.site_type = null;
      this.groups = [];
      this.direction_current_form = '';
      this.speciality = -1;
      this.hospital_research_department_pk = -1;
      if (this.pk >= 0) {
        this.$store.dispatch(actions.INC_LOADING);
        construct_point.researchDetails(this, 'pk').then((data) => {
          this.title = data.title;
          this.short_title = data.short_title;
          this.is_global_direction_params = data.is_global_direction_params;
          this.code = data.code;
          this.internal_code = data.internal_code;
          this.direction_current_form = data.direction_current_form;
          this.speciality = data.speciality;
          this.hospital_research_department_pk = data.department;
          this.info = data.info.replace(/<br\/>/g, '\n').replace(/<br>/g, '\n');
          this.hide = data.hide;
          this.site_type = data.site_type;
          this.loaded_pk = this.pk;
          this.groups = data.groups;
          this.direction_params_all = data.direction_params_all;
          this.direction_current_params = data.direction_current_params;
          this.assigned_to_params = data.assigned_to_params;
          if (this.groups.length === 0) {
            this.add_group();
          }
        }).finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
      } else {
        this.add_group();
      }
    },
    cancel() {
      // eslint-disable-next-line no-restricted-globals,no-alert
      if (this.has_unsaved && !confirm('Изменения, возможно, не сохранены. Вы уверены, что хотите отменить редактирование?')) {
        return;
      }
      this.cancel_do = true;
      this.$root.$emit('research-editor:cancel');
    },
    save() {
      this.$store.dispatch(actions.INC_LOADING);
      const props = [
        'pk',
        'department',
        'title',
        'short_title',
        'is_global_direction_params',
        'code',
        'hide',
        'groups',
        'site_type',
        'internal_code',
        'direction_current_form',
        'speciality',
        'hospital_research_department_pk',
        'direction_current_params',
      ];
      const moreData = {
        info: this.info.replace(/\n/g, '<br/>').replace(/<br>/g, '<br/>'),
        simple: this.simple,
      };
      if (this.simple) {
        props.push('main_service_pk', 'hide_main', 'hs_pk');
      }
      construct_point.updateResearch(this, props, moreData).then(() => {
        this.has_unsaved = false;
        window.okmessage('Сохранено');
        this.cancel();
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    async load_deparments() {
      const { data } = await api('procedural-list/suitable-departments');
      this.departments = [{ id: -1, label: 'Отделение не выбрано' }, ...data];
    },
  },
};
</script>

<style scoped lang="scss">
.modal-mask {
  align-items: stretch !important;
  justify-content: stretch !important;
}

::v-deep .panel-flt {
  margin: 41px;
  align-self: stretch !important;
  width: 100%;
  display: flex;
  flex-direction: column;
}

::v-deep .panel-body {
  flex: 1;
  padding: 0;
  height: calc(100% - 91px);
  min-height: 200px;
}

.top-editor {
  display: flex;
  flex: 0 0 68px;

  .left {
    flex: 0 0 45%
  }

  .right {
    flex: 0 0 55%
  }

  &.simpleEditor, &.formEditor {
    flex: 0 0 34px;

    .left {
      flex: 0 0 100%
    }

    .right {
      display: none;
    }
  }

  .left {
    border-right: 1px solid #96a0ad;
  }

  .input-group-addon {
    border-top: none;
    border-left: none;
    border-right: none;
    border-radius: 0;
  }

  .form-control {
    border-top: none;
    border-radius: 0;
  }

  .input-group > .form-control:last-child {
    border-right: none;
  }

  .f-code {
    padding: 6px;
  }
}

.content-editor {
  height: 100%;
}

.footer-editor {
  flex: 0 0 34px;
  display: flex;
  justify-content: flex-end;
  background-color: #f4f4f4;

  .btn {
    border-radius: 0;
  }
}

.top-editor, .content-editor, .footer-editor {
  align-self: stretch;
}

.root {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  align-content: stretch;
}

.content-editor {
  padding: 5px;
  overflow-y: auto;
}

.ed-group {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  background: #f0f0f0;
}

.groupHidden:not(:hover) {
  opacity: .6;
}

.ed-field {
  padding: 5px;
  margin: 5px;
  border-radius: 5px;
  background: #fff;
  color: #000;
}

.ed-field-inner {
  display: flex;
  flex-direction: row;
  align-items: stretch;
}

.ed-field-inner > div {
  align-self: stretch;

  textarea {
    resize: none;
  }

  &:nth-child(1) {
    flex: 0 0 35px;
    padding-right: 5px;
  }

  &:nth-child(2) {
    width: calc(100% - 530px);
  }

  &:nth-child(3), &:nth-child(4), &:nth-child(5), &:nth-child(6) {
    width: 140px;
    padding-left: 5px;
    padding-right: 5px;
    white-space: nowrap;

    label {
      display: block;
      margin-bottom: 2px;
      width: 100%;

      input[type="number"] {
        width: 100%;
      }
    }
  }

  &:nth-child(3), &:nth-child(4) {
    width: 180px;
  }
}

.lob {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.nob {
  border-radius: 0;
}

::v-deep .v-collapse-content-end {
  max-height: 10000px !important;
}

.vc-collapse ::v-deep .v-collapse-content {
  display: none;

  &.v-collapse-content-end {
    display: block;
  }
}

.department-select {
  margin-top: 5px;
}
</style>
