<template>
  <div style="height: 100%;width: 100%;position: relative" :class="[pay_source && !create_and_open && 'pay_source']">
    <div :class="['top-picker', need_vich_code && 'need-vich-code', hide_diagnosis && 'hide_diagnosis']" v-if="!simple">
      <button class="btn btn-blue-nb top-inner-btn" @click="clear_diagnos"
              v-if="!hide_diagnosis"
              v-tippy="{ placement : 'bottom', arrow: true }"
              title="Очистить диагноз">
        <span>&times;</span>
      </button>
      <m-k-b-field v-model="diagnos" v-if="!hide_diagnosis"/>
      <div class="vich-code" v-if="need_vich_code && !hide_diagnosis">
        <TypeAhead src="/api/vich_code?keyword=:keyword" :getResponse="getResponse" :onHit="onHitVich" ref="v"
                   placeholder="Код"
                   v-model="vich_code" maxlength="12" :delayTime="delayTime" :minChars="minChars"
                   :render="renderItems"
                   :limit="limit" :highlighting="highlighting" :selectFirst="selectFirst"
        />
      </div>
      <div class="top-inner">
        <a href="#" @click.prevent="select_fin(row.pk)" class="top-inner-select"
           :class="{ active: row.pk === fin}"
           :key="row.pk"
           v-for="row in base.fin_sources"><span>{{ row.title }}</span></a>
      </div>
    </div>
    <div :class="['content-picker', simple ? 'simple': '']" style="margin: 5px">
      <div v-if="Object.keys(researches_departments).length === 0"
           style="padding: 10px;color: gray;text-align: center;width: 100%;">
        Услуги не выбраны
      </div>
      <table class="table table-bordered table-condensed" style="table-layout: fixed; margin-bottom: 10px;">
        <colgroup>
          <col width="130">
          <col>
          <col width="38" v-if="!readonly">
        </colgroup>
        <tbody>
        <tr v-for="(row, key) in researches_departments" :key="key">
          <td>{{ row.title }}</td>
          <td class="pb0">
            <research-display v-for="(res, idx) in row.researches" :simple="simple"
                              :key="`${res.pk}_${hasNotFilled(res.pk)}`"
                              :title="res.title" :pk="res.pk" :n="idx"
                              :kk="kk"
                              :comment="(localizations[res.pk] || {}).label || comments[res.pk]"
                              :count="counts[res.pk]"
                              :service_location="(service_locations[res.pk] || {}).label"
                              :category="categories[res.site_type_raw]"
                              :has_not_filled="hasNotFilled(res.pk)"
                              :has_params="form_params[res.pk]"
                              :not_filled_fields="hasNotFilled(res.pk) ? r_list(form_params[res.pk]) : []"
                              :nof="row.researches.length"/>
          </td>
          <td v-if="!readonly" class="cl-td clean-btn-td">
            <button class="btn last btn-blue-nb nbr" type="button"
                    v-tippy="{ placement : 'bottom', arrow: true }"
                    :title="`Очистить категорию ${row.title}`" @click.prevent="clear_department(parseInt(key, 10))">
              <i class="fa fa-times"></i>
            </button>
          </td>
        </tr>
        <tr v-if="Object.keys(researches_departments).length > 1 && !readonly">
          <td colspan="2"></td>
          <td class="cl-td clean-btn-td">
            <button class="btn last btn-blue-nb nbr" type="button"
                    v-tippy="{ placement : 'bottom', arrow: true }"
                    title="Очистить всё" @click.prevent="clear_all">
              <i class="fa fa-times-circle"></i>
            </button>
          </td>
        </tr>
        </tbody>
      </table>
      <table class="table table-bordered table-condensed more-params" style="table-layout: fixed" v-if="show_additions">
        <colgroup>
          <col width="185">
          <col>
        </colgroup>
        <tbody>
        <tr v-if="direction_purpose_enabled && !hide_params">
          <th>Цель направления:</th>
          <td class="cl-td">
            <SelectFieldTitled v-model="direction_purpose" :variants="purposes"/>
          </td>
        </tr>
        <tr v-if="external_organizations_enabled && !hide_params">
          <th>Внешняя организация:</th>
          <td class="cl-td">
            <SelectFieldTitled v-model="external_organization" :variants="externalOrganizations"/>
          </td>
        </tr>
        <tr v-if="!has_only_stationar && !hide_params">
          <th>Кол-во повторений:</th>
          <td class="cl-td">
            <input v-model="directions_count" min="1" max="10"
                   style="max-width: 165px;display: inline-block;" class="form-control" type="number" step="1"
            />
            <span v-if="directions_count > 1" class="small">
              выбранное&nbsp;будет&nbsp;назначено&nbsp;{{
                directions_count
              }}&nbsp;раз{{ (directions_count === 0 || directions_count > 5) ? '' : 'а' }}
            </span>
          </td>
        </tr>
        <tr v-else-if="!hide_params">
          <th>Отделение стационара</th>
          <td class="cl-td">
            <treeselect :multiple="false" :disable-branch-nodes="true"
                        class="treeselect-noborder treeselect-wide"
                        :options="hospital_department_overrides" :append-to-body="true"
                        placeholder="По умолчанию" :clearable="false"
                        v-model="hospital_department_override"
            />
          </td>
        </tr>
        <tr v-if="directions_params_enabled">
          <td class="cl-td" v-if="global_current_direction_param !== -1">
            <button class="btn btn-blue-nb nbr full-inner-btn" @click="global_research_direction_param.show = true">
              Заполнить параметры
            </button>
          </td>
          <th v-else>
            Параметры:
          </th>
          <td class="cl-td">
            <treeselect :multiple="false" :disable-branch-nodes="true"
                        class="treeselect-noborder"
                        :options="global_direction_params" :append-to-body="true"
                        placeholder="Тип не выбран" :clearable="false"
                        v-model="global_current_direction_param"
            />
          </td>
        </tr>
        <tr v-if="directions_params_enabled && !r(global_research_direction_param)">
          <td colspan="2">
            <div class="status-list empty-block">
              <div class="status status-none">Не заполнены:&nbsp;</div>
              <div class="status status-none" :key="rl" v-for="rl in r_list(global_research_direction_param)">{{ rl }};</div>
            </div>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
    <div class="bottom-picker-inputs" v-if="pay_source && !create_and_open">
      <input v-model="count" placeholder="Количество" title="Количество"
             v-tippy="{ placement : 'top', arrow: true, followCursor: true, distance : 15 }"
             type="number" min="1" max="1000" class="form-control"/>
      <input v-model="discount" placeholder="Скидка"
             v-tippy="{ placement : 'top', arrow: true, followCursor: true, distance : 15 }"
             title="Скидка" type="number" min="0" max="100" class="form-control"/>
      <div class="bottom-picker-inputs-over">
        кол.<br/>
        -%
      </div>
    </div>
    <div class="bottom-picker" v-if="!simple">
      <template v-if="create_and_open">
        <button class="btn btn-blue-nb top-inner-select" :disabled="!can_save" @click="generate('create_and_open')"
                title="Сохранить и распечатать направления">
          <span>Сохранить и заполнить протокол</span>
        </button>
        <button class="btn btn-blue-nb top-inner-select" :disabled="!can_save" @click="generate('direction')"
                title="Сохранить и распечатать направления">
          <span>Сохранить и распечатать направления</span>
        </button>
      </template>
      <template v-else>
        <button class="btn btn-blue-nb top-inner-select" :disabled="!can_save" @click="generate('direction')"
                title="Сохранить и распечатать направления">
          <span>Сохранить и распечатать направления</span>
        </button>
        <button class="btn btn-blue-nb top-inner-select hidden-small" :disabled="!can_save"
                @click="generate('barcode')"
                title="Сохранить и распечатать штрих-коды">
          <span>Сохранить и распечатать штрих-коды</span>
        </button>
        <button class="btn btn-blue-nb top-inner-select" :disabled="!can_save" @click="generate('just-save')"
                title="Сохранить без печати">
          <span>Сохранить без печати</span>
        </button>
      </template>
    </div>

    <modal ref="modal" @close="cancel_update" show-footer="true"
           overflow-unset="true" resultsEditor
           v-show="visible && need_update_comment.length > 0 && !hide_window_update && !simple || show_global_direction_params">
      <span v-if="show_global_direction_params" slot="header">Настройка общих параметров для направления</span>
      <span v-else slot="header">Настройка назначений</span>
      <div slot="body" class="overflow-unset">
        <table v-if="!show_global_direction_params" class="table table-bordered table-responsive"
               style="table-layout: fixed;background-color: #fff;margin: 0 auto;">
          <colgroup>
            <col width="230">
            <col width="40">
            <col width="230">
            <col width="230">
            <col width="80">
          </colgroup>
          <thead>
          <tr>
            <th colspan="2">Назначение</th>
            <th>Комментарий</th>
            <th>Место</th>
            <th>Количество</th>
          </tr>
          </thead>
          <tbody>
          <template v-for="(row, i) in need_update_object">
            <!-- eslint-disable-next-line vue/require-v-for-key -->
            <tr>
              <td class="cl-td" :colspan="(need_update_object.length > 1 && i === 0) ? 1 : 2">
                <div style="width:100%; overflow: hidden; text-overflow: ellipsis;" :title="row.title">
                  <span v-if="row.direction_params > -1" title="Параметры направления" v-tippy>
                    <button type="button" class="btn btn-blue-nb nbr"
                            @click="form_params[row.pk].show = !form_params[row.pk].show">
                    <i v-if="form_params[row.pk].show" class="glyphicon glyphicon-arrow-up"></i>
                      <i v-else class="glyphicon glyphicon-arrow-down"></i>
                    </button>
                  </span>
                  <div style="display: inline-block; margin: 0 5px;">
                    {{ row.title }}
                  </div>
                  <div class="status-list empty-block" v-if="row.direction_params > -1 && !r(form_params[row.pk])">
                    <div class="status status-none">Не заполнены:&nbsp;</div>
                    <div class="status status-none" :key="rl" v-for="rl in r_list(form_params[row.pk])">{{ rl }};</div>
                  </div>
                </div>
              </td>
              <td class="cl-td" v-if="need_update_object.length > 1 && i === 0">
                <button class="btn last btn-blue-nb nbr" type="button"
                        v-tippy="{ placement : 'bottom', arrow: true }"
                        title="Назначить всем исследованиям те же параметры" @click="applyAllFromFirst">
                  <i class="fa fa-circle"></i>
                </button>
              </td>
              <td class="cl-td">
                <v-select :clearable="false" :options="row.localizations"
                          :searchable="false" v-if="row.localizations && row.localizations.length > 0"
                          v-model="localizations[row.pk]"/>
                <v-select :options="row.options" taggable v-else v-model="comments[row.pk]">
                  <div slot="no-options">Нет вариантов по умолчанию</div>
                </v-select>
              </td>
              <td class="cl-td">
                <v-select :clearable="false" :options="row.service_locations"
                          :searchable="false" v-if="row.service_locations && row.service_locations.length > 0"
                          v-model="service_locations[row.pk]"/>
                <div style="text-align: center;padding: 3px;color: lightslategray;font-size: 90%" v-else>
                  нет доступных вариантов
                </div>
              </td>
              <td class="cl-td">
                <input class="form-control" type="number" min="1" max="1000" v-model="counts[row.pk]"/>
              </td>
            </tr>
            <template v-if="form_params[row.pk]">
              <tr :key="row.pk">
                <td colspan="5">
                  <SelectedResearchesParams
                    :research="form_params[row.pk]"
                    :selected_card="selected_card"
                  />
                </td>
              </tr>
            </template>
          </template>
          </tbody>
        </table>
        <template v-else>
          <SelectedResearchesParams
            :research="global_research_direction_param"
            :selected_card="selected_card"
          />
        </template>
      </div>
      <div slot="footer" class="text-center">
        <button @click="cancel_update" class="btn btn-blue-nb">Закрыть</button>
      </div>
    </modal>
  </div>
</template>

<script>
import vSelect from 'vue-select';
import _ from 'lodash';
import { vField, vGroup } from '@/components/visibility-triggers';
import api from '@/api';
import Treeselect from '@riophae/vue-treeselect';
import TypeAhead from 'vue2-typeahead';
import directionsPoint from '../api/directions-point';
import * as actions from '../store/action-types';
import ResearchDisplay from './ResearchDisplay.vue';
import Modal from './Modal.vue';
import 'vue-select/dist/vue-select.css';
import MKBField from '../fields/MKBField.vue';
import SelectFieldTitled from '../fields/SelectFieldTitled.vue';
import SelectedResearchesParams from './SelectedResearchesParams.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  name: 'selected-researches',
  components: {
    SelectFieldTitled,
    ResearchDisplay,
    Modal,
    vSelect,
    TypeAhead,
    MKBField,
    SelectedResearchesParams,
    Treeselect,
  },
  props: {
    simple: {
      type: Boolean,
      default: false,
    },
    researches: {
      type: Array,
      required: true,
    },
    base: {
      type: Object,
    },
    card_pk: {
      type: Number,
    },
    selected_card: {
      type: Object,
    },
    visible: {
      type: Boolean,
      default: true,
    },
    operator: {
      type: Boolean,
      default: false,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    hide_diagnosis: {
      type: Boolean,
      default: false,
    },
    hide_params: {
      type: Boolean,
      default: false,
    },
    create_and_open: {
      type: Boolean,
      default: false,
    },
    ofname: {
      type: Number,
      default: -1,
    },
    history_num: {
      type: String,
      default: '',
    },
    main_diagnosis: {
      type: String,
      default: '',
    },
    kk: {
      type: String,
      default: '',
    },
    initial_fin: {
      default: null,
    },
    parent_iss: {
      default: null,
    },
    parent_slave_iss: {
      default: null,
    },
    clear_after_gen: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      diagnos: '',
      fin: -1,
      comments: {},
      form_params: {},
      localizations: {},
      counts: {},
      global_direction_params: [{ id: -1, label: 'Не выбрано' }],
      global_current_direction_param: -1,
      global_research_direction_param: {},
      hospital_department_overrides: [{ id: -1, label: 'По умолчанию' }],
      hospital_department_override: -1,
      service_locations: {},
      need_update_comment: [],
      need_update_localization: [],
      need_update_service_location: [],
      need_update_direction_params: [],
      hide_window_update: false,
      delayTime: 300,
      minChars: 1,
      limit: 11,
      selectFirst: true,
      vich_code: '',
      count: 1,
      discount: 0,
      purposes: [],
      externalOrganizations: [],
      direction_purpose: 'NONE',
      external_organization: 'NONE',
      directions_count: '1',
      researches_direction_params: {},
    };
  },
  watch: {
    directions_count() {
      if (this.directions_count.trim() === '') {
        return;
      }

      let nd = Number(this.directions_count) || 1;

      if (nd < 1) {
        nd = 1;
      }
      if (nd > 10) {
        nd = 10;
      }

      this.directions_count = String(nd);
    },
    count() {
      this.count = Math.min(Math.max(parseInt(this.count, 10) || 1, 1), 1000);
    },
    discount() {
      this.discount = Math.min(Math.max(parseInt(this.discount, 10) || 0, 0), 100);
    },
    card_pk() {
      this.clear_fin();
    },
    base() {
      this.fin = -1;
    },
    async researches() {
      const comments = {};
      const form_params = {};
      const service_locations = {};
      const localizations = {};
      const counts = {};
      this.need_update_comment = this.need_update_comment.filter((e) => this.researches.indexOf(e) !== -1);
      this.need_update_localization = this.need_update_localization.filter((e) => this.researches.indexOf(e) !== -1);
      this.need_update_service_location = this.need_update_service_location.filter((e) => this.researches.indexOf(e) !== -1);
      this.need_update_direction_params = this.need_update_direction_params.filter((e) => this.researches.indexOf(e) !== -1);
      let needShowWindow = false;
      for (const pk of this.researches) {
        if (!this.comments[pk] && !this.localizations[pk] && !this.service_locations[pk] && !this.form_params[pk]) {
          comments[pk] = '';
          if (pk in this.$store.getters.researches_obj) {
            const res = this.$store.getters.researches_obj[pk];
            if (res.comment_variants.length > 0) {
              comments[pk] = JSON.parse(JSON.stringify(res.comment_variants[0]));

              if (res.comment_variants.length > 1 && !this.need_update_comment.includes(pk)) {
                this.need_update_comment.push(pk);
                needShowWindow = true;
              }
            }

            if (res.localizations && res.localizations.length > 0) {
              // eslint-disable-next-line prefer-destructuring
              localizations[pk] = res.localizations[0];

              if (res.localizations.length > 1 && !this.need_update_localization.includes(pk)) {
                this.need_update_localization.push(pk);
                needShowWindow = true;
              }
            }

            if (res.service_locations && res.service_locations.length > 0) {
              // eslint-disable-next-line prefer-destructuring
              service_locations[pk] = res.service_locations[0];

              if (res.service_locations.length > 1 && !this.need_update_service_location.includes(pk)) {
                this.need_update_service_location.push(pk);
                needShowWindow = true;
              }
            }

            if (this.directions_params_enabled) {
              if (res.direction_params > -1 && !this.need_update_direction_params.includes(pk) && !this.form_params[pk]) {
                this.need_update_direction_params.push(pk);
                this.form_params[pk] = {};
                needShowWindow = true;
                form_params[pk] = _.cloneDeep(
                  await this.load_direction_params_data(res.direction_params),
                );
                form_params[pk].show = true;
              } else if (this.form_params[pk]) {
                form_params[pk] = this.form_params[pk];
              }
            }
          }

          counts[pk] = 1;
        } else {
          comments[pk] = this.comments[pk];
          localizations[pk] = this.localizations[pk];
          service_locations[pk] = this.service_locations[pk];
          counts[pk] = this.counts[pk];
          form_params[pk] = this.form_params[pk];
        }
      }
      this.comments = comments;
      this.form_params = form_params;
      this.localizations = localizations;
      this.service_locations = service_locations;
      this.counts = counts;
      if (needShowWindow) {
        this.show_window();
        this.$forceUpdate();
      }
    },
    comments: {
      deep: true,
      handler() {
        for (const k of Object.keys(this.comments)) {
          if (this.comments[k] && this.comments[k].length > 40) {
            this.comments[k] = this.comments[k].substr(0, 40);
          }
        }
      },
    },
    diagnos() {
      if (/^[a-zA-Zа-яА-Я]\d.*/g.test(this.diagnos)) {
        this.diagnos = this.diagnos.toUpperCase();
        const replace = ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ',
          'ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э',
          'я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю'];

        const search = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '\\[', '\\]',
          'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'',
          'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.'];

        for (let i = 0; i < replace.length; i++) {
          const reg = new RegExp(replace[i], 'mig');
          this.diagnos = this.diagnos.replace(
            reg,
            (a) => (a === a.toLowerCase() ? search[i] : search[i].toUpperCase()),
          );
        }
      }
      this.$root.$emit('update_diagnos', this.diagnos);
    },
    fin() {
      this.$root.$emit('update_fin', this.fin);
    },
    direction_purpose_enabled: {
      immediate: true,
      handler() {
        if (this.direction_purpose_enabled) {
          this.load_direction_purposes();
        }
      },
    },
    external_organizations_enabled: {
      immediate: true,
      handler() {
        if (this.external_organizations_enabled) {
          this.load_external_organizations();
        }
      },
    },
    global_current_direction_param() {
      this.changeSelectGlobalResearchDirectionParam(this.global_current_direction_param);
    },
    external_organization(a) {
      if (!this.directions_params_enabled) {
        return;
      }
      const paramsPk = Number(this.directions_params_org_form_default_pk);
      const params = this.global_direction_params.find(({ id }) => Number(id) === paramsPk);
      if (!params) {
        return;
      }
      if (a !== 'NONE') {
        this.global_current_direction_param = params.id;
      } else if (this.global_current_direction_param === params.id) {
        this.global_current_direction_param = -1;
      }
    },
  },
  mounted() {
    this.$root.$on(`researches-picker:clear_all${this.kk}`, this.clear_all);
    this.$root.$on(`researches-picker:update-comment${this.kk}`, this.update_comment);
    this.$root.$on(`patient-picker:select_card${this.kk}`, this.clear_diagnos);
    if (this.initial_fin) {
      this.select_fin(this.initial_fin);
    }
    this.load_direction_params();
    this.load_stationar_deparments();
  },
  methods: {
    async changeSelectGlobalResearchDirectionParam(pk) {
      if (!this.researches_direction_params[pk]) {
        this.global_research_direction_param = {};
        return;
      }
      this.global_research_direction_param = _.cloneDeep(
        await this.load_direction_params_data(pk),
      );
      this.global_research_direction_param.show = true;
    },
    async load_direction_params() {
      const data = await api('researches/by-direction-params');
      this.global_direction_params = [
        { id: -1, label: 'Не выбрано' },
        ...Object.keys(data).map((id) => ({ id, label: data[id].title })),
      ];
      this.researches_direction_params = data;
    },
    async load_direction_params_data(pk) {
      if (
        this.researches_direction_params[pk]
        && this.researches_direction_params[pk].research_data
        && this.researches_direction_params[pk].research_data.research
        && this.researches_direction_params[pk].research_data.research.status !== 'NOT_LOADED'
      ) {
        return this.researches_direction_params[pk].research_data.research;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      if (!this.researches_direction_params[pk]) {
        this.researches_direction_params[pk] = {};
      }
      if (!this.researches_direction_params[pk].research_data) {
        this.researches_direction_params[pk].research_data = {};
      }
      this.researches_direction_params[pk].research_data.research = await api('researches/get-direction-params', { pk });
      await this.$store.dispatch(actions.DEC_LOADING);
      return this.researches_direction_params[pk].research_data.research;
    },
    hasNotFilled(pk) {
      return this.form_params[pk] && !this.r(this.form_params[pk]);
    },
    applyAllFromFirst() {
      const { pk: fpk } = this.need_update_object[0];
      for (const row of this.need_update_object.slice(1)) {
        if (
          this.localizations[fpk]
          && (row.localizations || []).find(({ code }) => code === this.localizations[fpk].code)
        ) {
          this.localizations[row.pk] = this.localizations[fpk];
        }
        if ((row.options || []).includes(this.comments[fpk]) || this.comments[fpk] === '') {
          this.comments[row.pk] = this.comments[fpk];
        }
        if (
          this.service_locations[fpk]
          && (row.service_locations || []).find(
            ({ code }) => code === this.service_locations[fpk].code,
          )
        ) {
          this.service_locations[row.pk] = this.service_locations[fpk];
        }
      }
    },
    update_comment(pk) {
      if (this.need_update_comment.indexOf(pk) === -1) {
        this.need_update_comment.push(pk);
      }
      this.show_window();
    },
    cancel_update() {
      this.need_update_comment = [];
      this.need_update_localization = [];
      this.need_update_service_location = [];
      this.need_update_direction_params = [];
      this.hide_window();
      if (this.global_research_direction_param) {
        this.global_research_direction_param.show = false;
      }
    },
    onHit(item) {
      this.diagnos = item.split(' ')[0] || '';
    },
    onHitVich(item) {
      this.vich_code = item.split(' ')[0] || '';
    },
    getResponse(resp) {
      return [...resp.data.data];
    },
    renderItems: (items) => items.map((i) => `${i.code} ${i.title}`),
    get_def_diagnosis(finOrig) {
      const fin = finOrig || this.fin;
      return (`${this.main_diagnosis} ${this.get_fin_obj(fin).default_diagnos}`).trim();
    },
    clear_diagnos() {
      this.diagnos = this.get_def_diagnosis();
      this.vich_code = '';
    },
    highlighting: (item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`),
    hide_window() {
      this.hide_window_update = true;
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
    },
    show_window() {
      this.hide_window_update = false;
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'block';
      }
    },
    researches_departments_simple() {
      const r = {};

      for (const pk of this.researches) {
        if (pk in this.$store.getters.researches_obj) {
          const res = this.$store.getters.researches_obj[pk];
          if (!(res.department_pk in r)) {
            r[res.department_pk] = [];
          }
          r[res.department_pk].push(pk);
        }
      }
      return r;
    },
    get_fin_obj(pk) {
      if (pk !== -1) {
        for (const f of this.base.fin_sources) {
          if (f.pk === pk) return f;
        }
      }
      return { pk: -1, title: '', default_diagnos: '' };
    },
    select_fin(pkOrig) {
      let pk = pkOrig;
      if (this.base.fin_sources.length === 1 && pk === -1) {
        pk = this.base.fin_sources[0].pk;
      }
      const cfin = this.fin;
      this.fin = pk;
      this.count = 1;
      this.discount = 0;
      if (this.get_def_diagnosis(cfin) === this.diagnos || this.diagnos.trim() === '') {
        this.diagnos = this.get_def_diagnosis();
      }
    },
    clear_department(pk) {
      this.$root.$emit(`researches-picker:deselect_department${this.kk}`, pk);
    },
    generate(type) {
      if (this.diagnos === '' && this.current_fin !== 'Платно' && !this.pay_source && !this.create_and_open) {
        window.$(this.$refs.d).focus();
        window.errmessage('Диагноз не указан', 'Если не требуется, то укажите прочерк ("-")');
        return;
      }
      if (this.need_vich_code && this.vich_code === '') {
        window.$(this.$refs.v).focus();
        window.errmessage('Не указан код', 'Требуется код для направления на ВИЧ');
        return;
      }
      this.$root.$emit('generate-directions', {
        type,
        card_pk: this.card_pk,
        fin_source_pk: this.fin,
        diagnos: this.diagnos.substr(0, 200),
        base: this.base,
        researches: this.researches_departments_simple(),
        operator: this.operator,
        ofname: this.ofname,
        history_num: this.history_num,
        comments: this.comments,
        counts: this.counts,
        localizations: this.localizations,
        service_locations: this.service_locations,
        vich_code: this.need_vich_code ? this.vich_code : '',
        count: this.count,
        discount: this.discount,
        need_contract: this.pay_source,
        parent_iss: this.parent_iss,
        parent_slave_hosp: this.parent_slave_iss,
        kk: this.kk,
        direction_purpose: this.direction_purpose,
        external_organization: this.external_organization,
        directions_count: Number(this.directions_count) || 1,
        direction_form_params: this.form_params,
        current_global_direction_params: this.global_research_direction_param,
        hospital_department_override: this.hospital_department_override,
      });
    },
    clear_all() {
      this.$root.$emit(`researches-picker:deselect_all${this.kk}`);
      this.clear_fin();
      this.direction_purpose = 'NONE';
      this.external_organization = 'NONE';
      this.directions_count = '1';
      this.global_current_direction_param = -1;
      this.hospital_department_override = -1;
    },
    clear_fin() {
      this.select_fin(-1);
    },
    async load_direction_purposes() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { purposes } = await directionsPoint.getPurposes();
      this.purposes = purposes;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async load_external_organizations() {
      if (!this.external_organizations_enabled) {
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      const { organizations } = await directionsPoint.getExternalOrgranizations();
      this.externalOrganizations = organizations;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    r(research) {
      if (!research) {
        return true;
      }
      return this.r_list(research).length === 0;
    },
    r_list(research) {
      if (!research.groups) {
        return [];
      }
      const l = [];
      for (const g of research.groups) {
        if (!vGroup(g, research.groups, this.simulated_patient)) {
          continue;
        }
        let n = 0;
        for (const f of g.fields) {
          n++;
          if (f.required && (f.value === '' || f.value === '- Не выбрано' || !f.value)
            && (vField(g, research.groups, f.visibility, this.simulated_patient))) {
            l.push((g.title !== '' ? `${g.title} ` : '') + (f.title === '' ? `поле ${n}` : f.title));
          }
        }
      }
      return l.slice(0, 2);
    },
    is_stationar(pk) {
      const res = this.$store.getters.researches_obj[pk] || {};
      return res.department_pk === -5;
    },
    async load_stationar_deparments() {
      const { data } = await api('procedural-list/suitable-departments');
      this.hospital_department_overrides = [{ id: -1, label: 'По умолчанию' }, ...data];
    },
  },
  computed: {
    has_stationar() {
      for (const pk of this.researches) {
        if (this.is_stationar(pk)) {
          return true;
        }
      }
      return false;
    },
    has_only_stationar() {
      for (const pk of this.researches) {
        if (!this.is_stationar(pk)) {
          return false;
        }
      }
      return true;
    },
    show_global_direction_params() {
      return this.global_research_direction_param && this.global_research_direction_param.show;
    },
    direction_purpose_enabled() {
      return this.$store.getters.modules.l2_direction_purpose && this.kk !== 'stationar';
    },
    external_organizations_enabled() {
      return this.$store.getters.modules.l2_external_organizations && this.kk !== 'stationar';
    },
    directions_params_enabled() {
      return this.$store.getters.modules.directions_params && this.kk !== 'stationar';
    },
    l2_user_data() {
      return this.$store.getters.user_data || {};
    },
    directions_params_org_form_default_pk() {
      return this.l2_user_data.directions_params_org_form_default_pk;
    },
    show_additions() {
      return this.researches.length > 0;
    },
    current_fin() {
      return this.get_fin_obj(this.fin);
    },
    pay_source() {
      return this.current_fin.title.toLowerCase() === 'платно';
    },
    researches_departments() {
      const r = {};
      const deps = {
        '-2': { title: 'Консультации' },
        '-3': { title: 'Лечение' },
        '-4': { title: 'Стоматология' },
        '-5': { title: 'Стационар' },
        '-9998': { title: 'Морфология' },
        '-9': { title: 'Формы' },
      };
      for (const dep of this.$store.getters.allDepartments) {
        deps[dep.pk] = dep;
      }

      for (const pk of this.researches) {
        if (this.$store.getters.researches_obj[pk]) {
          const res = this.$store.getters.researches_obj[pk];
          const d = (res.department_pk && !res.doc_refferal) ? res.department_pk : -2;
          if (!(d in r)) {
            r[d] = {
              pk: d,
              title: deps[d].title,
              researches: [],
            };
          }
          r[d].researches.push({ pk, title: res.title, site_type_raw: res.site_type_raw });
        }
      }
      return r;
    },
    categories() {
      const sc = this.$store.getters.ex_dep[8] || [];
      return sc.reduce((a, b) => ({ ...a, [b.pk]: b.title }), {});
    },
    need_vich_code() {
      for (const pk of this.researches) {
        if (
          pk in this.$store.getters.researches_obj
          && this.$store.getters.researches_obj[pk].need_vich_code
        ) {
          return true;
        }
      }
      return false;
    },
    can_save() {
      if (this.fin === -1 || this.researches.length === 0 || this.card_pk === -1) {
        return false;
      }

      if (!this.r(this.global_research_direction_param)) {
        return false;
      }

      return !this.researches.find((pk) => {
        if (!this.form_params[pk]) {
          return false;
        }

        return !this.r(this.form_params[pk]);
      });
    },
    need_update_object() {
      const r = [];
      const toUpd = [...this.need_update_comment];
      for (const pk of [
        ...this.need_update_localization,
        ...this.need_update_service_location,
        ...this.need_update_direction_params,
      ]) {
        if (!toUpd.includes(pk)) {
          toUpd.push(pk);
        }
      }
      for (const pk of toUpd) {
        if (pk in this.$store.getters.researches_obj) {
          const res = this.$store.getters.researches_obj[pk];
          r.push({
            pk,
            title: res.title,
            options: res.comment_variants,
            localizations: res.localizations,
            service_locations: res.service_locations,
            direction_params: res.direction_params,
            research_data: res.research_data.research,
          });
        }
      }
      return r;
    },
  },
};
</script>

<style scoped lang="scss">
.top-picker, .bottom-picker {
  height: 34px;
  background-color: #AAB2BD;
  position: absolute;
  left: 0;
  right: 0;
}

.top-picker {
  top: 0;
}

.top-inner, .content-picker, .bottom-picker {
  display: flex;
  flex-wrap: wrap;
  justify-content: stretch;
  align-content: center;
  align-items: stretch;
  overflow-y: auto;
}

.content-picker {
  align-content: flex-start;
}

.top-inner-btn {
  position: absolute;
  left: 180px;
  top: 0;
  bottom: 0;
  width: 35px;
  text-align: center;
  border-radius: 0;
}

.top-inner {
  position: absolute;
  left: 215px;
  top: 0;
  right: 0;
  height: 34px;
  align-content: stretch;
  overflow: hidden;
}

.need-vich-code .top-inner {
  left: 305px;
}

.hide_diagnosis .top-inner {
  left: 0;
}

.top-picker ::v-deep .form-control {
  border-radius: 0 !important;
  border: none;
  border-bottom: 1px solid #AAB2BD;

  &:first-child {
    width: 180px;
  }
}

.vich-code {
  position: absolute;
  width: 90px;
  left: 215px;
  top: 0;
}

.top-picker .vich-code ::v-deep .form-control {
  width: 90px;
}

.top-picker ::v-deep .input-group {
  border-radius: 0;
}

.top-picker ::v-deep ul {
  width: auto;
  right: -250px;
  font-size: 13px;
}

.top-picker ::v-deep ul li {
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 2px .25rem;
  margin: 0 .2rem;

  a {
    padding: 2px 10px;
  }
}

.top-inner-select, .top-inner-select.btn {
  border-radius: 0;
  border: none !important;
  align-self: stretch;
  display: flex;
  align-items: center;
  padding: 1px 2px 1px;
  text-decoration: none;
  cursor: pointer;
  flex: 1;
  margin: 0;
  font-size: 12px;
  min-width: 0;
  background-color: #AAB2BD;
  color: #fff;

  &:hover {
    background-color: #434a54;
  }

  &.active {
    background: #049372 !important;
    color: #fff;
  }

  &:disabled {
    color: #fff;
    cursor: not-allowed;
    opacity: .8;
    background-color: rgba(255, 255, 255, .7) !important;
  }

  span {
    display: block;
    text-overflow: ellipsis;
    overflow: hidden;
    word-break: keep-all;
    max-height: 2.2em;
    line-height: 1.1em;
    margin: 0 auto;
  }
}

.research-select {
  flex: 0 1 auto;
  width: 25%;
  height: 34px;
  border: 1px solid #6C7A89 !important;
}

.research-select:hover {
  box-shadow: inset 0 0 8px rgba(0, 0, 0, .8) !important;
}

.content-picker, .content-none {
  position: absolute;
  top: 0;
  bottom: 0;

  &:not(.simple) {
    top: 34px;
    bottom: 34px;
  }

  left: 0;
  right: 0;
  overflow-y: auto;
}

.bottom-picker {
  bottom: 0;
  left: 0;
  align-content: stretch;
  overflow: hidden;
}

.bottom-picker-inputs {
  position: absolute;
  bottom: 0;
  left: 0;
  padding-left: 25px;
  align-content: stretch;
  overflow: hidden;
  right: calc(100% - 70px);
  display: flex;
  flex-direction: column;

  .form-control {
    width: 100%;
    border-bottom: 0;
    border-left: 0;
    border-right: 0;
    border-radius: 0;
    padding-left: 5px;
    height: 17px;
    padding-right: 3px;
  }

  .bottom-picker-inputs-over {
    background: #aab2bd;
    color: #fff;
    line-height: 17px;
    position: absolute;
    left: 0;
    bottom: 0;
    right: calc(100% - 25px);
    font-size: 12px;
    padding-left: 1px;
  }
}

.pay_source .bottom-picker {
  left: 70px;
}

.bottom-picker .top-inner-select span {
  margin: 0 auto;
  text-align: center;
}

.bottom-picker-inputs {
  display: flex;
  flex-wrap: wrap;
  justify-content: stretch;
  align-content: center;
  align-items: stretch;
  overflow-y: auto;
}

.pb0 {
  padding-bottom: 0;
  padding-top: 4px;
}

.more-params {
  select, input, ::v-deep select, ::v-deep input {
    border-radius: 0;
    border: none;
  }
}

.status-list {
  display: flex;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status {
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-none {
  color: #CF3A24
}

.empty-block {
  border-radius: 4px;
  border: 1px solid #CF3A24;
  background: rgba(#CF3A24, .1);
  padding: 3px;
  margin: 3px;
}

.clean-btn-td .btn {
  width: 40px;
}

.full-inner-btn {
  display: block;
  width: 100%;
  height: 37px;
}
</style>
