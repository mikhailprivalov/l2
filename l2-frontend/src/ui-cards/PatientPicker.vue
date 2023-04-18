<template>
  <div style="height: 100%; width: 100%; position: relative">
    <div
      class="top-picker"
      :class="{ internalType: selected_base.internal_type }"
    >
      <div class="input-group">
        <div
          v-if="bases.length > 1"
          class="input-group-btn"
        >
          <button
            class="btn btn-blue-nb btn-ell dropdown-toggle nbr base-toggle"
            type="button"
            data-toggle="dropdown"
          >
            <span class="caret" /> {{ selected_base.title }}
          </button>
          <ul class="dropdown-menu">
            <li
              v-for="row in basesFiltered"
              :key="row.pk"
            >
              <a
                href="#"
                @click.prevent="select_base(row.pk)"
              >{{ row.title }}</a>
            </li>
          </ul>
        </div>
        <div
          v-else
          class="input-group-btn"
        >
          <button
            class="btn btn-blue-nb btn-ell dropdown-toggle nbr"
            type="button"
            data-toggle="dropdown"
            style="max-width: 200px; text-align: left !important"
          >
            {{ selected_base.title }}
          </button>
        </div>
        <div>
          <div class="autocomplete">
            <input
              ref="q"
              v-model="query"
              type="text"
              class="form-control bob"
              placeholder="Введите запрос - пример: Иванов Иван 01011970"
              maxlength="255"
              @keyup.enter="search"
              @keypress="keypress"
              @keydown="keypress_arrow"
              @click="click_input"
              @blur="blur"
              @keyup.esc="suggests.open = false"
              @focus="suggests_focus"
            >
            <div
              class="clear-input"
              :class="{ display: query.length > 0 }"
              @click="clear_input"
            >
              <i class="fa fa-times" />
            </div>
            <div
              v-if="(suggests.open && normalized_query.length > 0) || suggests.loading"
              class="suggestions"
            >
              <div
                v-if="suggests.loading && suggests.data.length === 0"
                class="item"
              >
                поиск...
              </div>
              <div
                v-else-if="suggests.data.length === 0"
                class="item"
              >
                не найдено карт в {{ system }}, попробуйте произвести поиск по ТФОМС или РМИС
              </div>
              <template v-else>
                <div
                  v-for="(row, i) in suggests.data"
                  :key="row.pk"
                  class="item item-selectable"
                  :class="{ 'item-selectable-focused': i === suggests.focused }"
                  @mouseover="suggests.focused = i"
                  @click.stop="select_suggest(i)"
                >
                  {{ row.family }} {{ row.name }} {{ row.twoname }}, {{ row.sex }}, {{ row.birthday }} ({{ row.age }})
                  <div>
                    <span
                      class="b"
                      style="display: inline-block; margin-right: 4px"
                    > {{ row.type_title }} {{ row.num }} </span>
                    <span
                      v-for="d in row.docs"
                      :key="d.pk"
                      class="item-doc"
                    >
                      {{ d.type_title }}: {{ d.serial }} {{ d.number }};
                    </span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
        <span
          v-if="tfoms_query"
          class="rmis-search input-group-btn"
        >
          <label
            class="btn btn-blue-nb nbr height34"
            style="padding: 5px 12px"
          >
            <input
              v-model="inc_tfoms"
              type="checkbox"
            >
            {{ tfoms_as_l2 ? 'ЕРЦП' : 'ТФОМС' }}
          </label>
        </span>
        <span
          v-if="selected_base.internal_type && user_data.rmis_enabled"
          class="rmis-search input-group-btn"
        >
          <label
            class="btn btn-blue-nb nbr height34"
            style="padding: 5px 12px"
          >
            <input
              v-model="inc_rmis"
              type="checkbox"
            > Вкл. РМИС
          </label>
        </span>
        <span class="input-group-btn">
          <button
            class="btn last btn-blue-nb nbr"
            type="button"
            :disabled="!query_valid || inLoading"
            @click="search({ source: 'button' })"
          >
            Поиск
          </button>
        </span>
      </div>
    </div>
    <div class="content-picker scrolldown">
      <div style="padding-left: 5px; padding-right: 5px">
        <table class="table table-bordered">
          <colgroup>
            <col width="124">
            <col>
            <col width="54">
            <col>
          </colgroup>
          <tbody>
            <tr>
              <td
                style="max-width: 124px"
                class="table-header-row"
              >
                ФИО:
              </td>
              <td
                style="max-width: 99%"
                class="table-content-row"
              >
                {{ selected_card.family }} {{ selected_card.name }} {{ selected_card.twoname }}
              </td>
              <td
                style="max-width: 54px"
                class="table-header-row"
              >
                {{ selected_card.is_rmis ? 'ID' : 'Карта' }}:
              </td>
              <td
                style="max-width: 99%"
                class="table-content-row"
              >
                {{ selected_card.num }}
                <span
                  v-if="selected_card.isArchive"
                  class="is-archive"
                >в архиве</span>
              </td>
            </tr>
            <tr>
              <td class="table-header-row">
                Дата рождения:
              </td>
              <td class="table-content-row">
                {{ selected_card.birthday }}<span v-if="loaded"> ({{ selected_card.age }})</span>
              </td>
              <td class="table-header-row">
                Пол:
              </td>
              <td class="table-content-row">
                {{ selected_card.sex }}
              </td>
            </tr>
            <tr v-if="!hide_card_editor">
              <td class="table-header-row">
                <span
                  v-if="history_n === 'true'"
                  class="hospital"
                  style="display: block; line-height: 1.2"
                >Номер истории:</span>
              </td>
              <td class="table-content-row">
                <div
                  v-if="history_n === 'true'"
                  style="height: 34px"
                >
                  <span class="hospital">
                    <input
                      v-model="history_num"
                      type="text"
                      class="form-control"
                      maxlength="11"
                      :disabled="!selected_base.history_number"
                    >
                  </span>
                </div>
              </td>
              <td colspan="2">
                <div
                  v-if="selected_base.internal_type && l2_cards"
                  class="internal_type"
                >
                  <button
                    v-if="selected_card.pk && l2_vaccine"
                    v-tippy="{ placement: 'bottom' }"
                    class="btn last btn-blue-nb nbr"
                    type="button"
                    title="Вакцинация"
                    @click="open_vaccine"
                  >
                    В
                  </button>
                  <button
                    v-if="selected_card.pk && selected_card.status_disp && selected_card.status_disp !== 'notneed'"
                    ref="disp"
                    v-tippy="{
                      placement: 'bottom',
                      reactive: true,
                      theme: 'light bordered',
                      duration: 0,
                      arrow: true,
                      sticky: true,
                      popperOptions: {
                        modifiers: {
                          preventOverflow: {
                            enabled: false,
                          },
                          hide: {
                            enabled: false,
                          },
                        },
                      },
                      trigger: 'click',
                      interactive: true,
                      html: '#template-disp',
                    }"
                    class="btn last btn-blue-nb nbr"
                    :class="{ [`dsp_${selected_card.status_disp}`]: true }"
                    type="button"
                  >
                    Д
                  </button>
                  <div
                    v-if="selected_card.pk && selected_card.status_disp && selected_card.status_disp !== 'notneed'"
                    id="template-disp"
                    class="dsp"
                  >
                    <strong>Диспансеризация</strong><br>
                    <ul style="padding-left: 25px; text-align: left">
                      <!-- eslint-disable-next-line vue/require-v-for-key -->
                      <li v-for="d in selected_card.disp_data">
                        <span :class="{ disp_row: true, [!!d[2] ? 'dsp_row_finished' : 'dsp_row_need']: true }">
                          <span v-if="!d[2]">требуется</span>
                          <a
                            v-else
                            href="#"
                            class="not-black"
                            @click.prevent="show_results([d[2]])"
                          > пройдено </a>
                        </span>

                        <a
                          href="#"
                          @click.prevent="add_researches([d[0]])"
                        >
                          {{ d[5] }}
                        </a>
                      </li>
                    </ul>
                    <div>
                      <a
                        v-if="selected_card.status_disp === 'need'"
                        href="#"
                        class="btn btn-blue-nb"
                        @click.prevent="
                          add_researches(
                            selected_card.disp_data.filter((d) => !d[2]).map((d) => d[0]),
                            true,
                          )
                        "
                      >
                        Выбрать требуемые
                      </a>
                      <a
                        v-else
                        href="#"
                        class="btn btn-blue-nb"
                        @click.prevent="show_results(selected_card.disp_data.map((d) => d[2]))"
                      >
                        Печать всех результатов
                      </a>
                    </div>
                  </div>
                  <button
                    v-if="l2_benefit && selected_card.pk"
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    class="btn last btn-blue-nb nbr"
                    type="button"
                    title="Льготы пациента"
                    @click="open_benefit()"
                  >
                    <i class="fa fa-cubes" />
                  </button>
                  <button
                    v-if="is_l2_cards && selected_card.pk"
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    class="btn last btn-blue-nb nbr"
                    type="button"
                    title="Диспансерный учёт"
                    @click="open_dreg()"
                  >
                    <i class="fa fa-database" />
                  </button>
                  <button
                    v-if="is_l2_cards && selected_card.pk"
                    v-tippy="{ placement: 'bottom' }"
                    class="btn last btn-blue-nb nbr"
                    type="button"
                    title="Произвольные записи о пациенте"
                    @click="open_ambulatory_data"
                  >
                    <i class="fa fa-user" />
                  </button>
                  <button
                    v-if="is_l2_cards && selected_card.pk"
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    class="btn last btn-blue-nb nbr"
                    type="button"
                    title="Анамнез жизни"
                    @click="open_anamnesis()"
                  >
                    <i class="fa fa-book" />
                  </button>
                  <button
                    v-if="is_l2_cards && allow_l2_card_edit"
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    class="btn last btn-blue-nb nbr"
                    type="button"
                    :title="`Новая ${system} карта`"
                    @click="open_editor(true)"
                  >
                    <i class="fa fa-plus" />
                  </button>
                  <button
                    v-if="is_l2_cards && allow_l2_card_edit"
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    class="btn last btn-blue-nb nbr"
                    type="button"
                    title="Редактирование карты"
                    style="margin-left: -1px"
                    :disabled="!selected_card.pk"
                    @click="open_editor()"
                  >
                    <i class="glyphicon glyphicon-pencil" />
                  </button>
                </div>
                <div
                  v-else-if="l2_cards && allow_l2_card_edit"
                  class="internal_type"
                >
                  <button
                    v-tippy="{ placement: 'bottom', arrow: true }"
                    class="btn last btn-blue-nb nbr"
                    type="button"
                    :title="`Открыть пациента в базе ${system}`"
                    style="margin-left: -1px"
                    :disabled="!selected_card.pk"
                    @click="open_as_l2_card()"
                  >
                    {{ system }}
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="directive_from_need === 'true'">
              <td
                class="table-header-row"
                style="line-height: 1"
              >
                Работа от имени:
              </td>
              <td class="cl-td">
                <Treeselect
                  v-model="directive_department"
                  class="treeselect-noborder treeselect-wide"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="directive_departments_select"
                  placeholder="Подразделение не выбрано"
                  :append-to-body="true"
                  :clearable="false"
                />
              </td>
              <td
                class="cl-td"
                colspan="2"
              >
                <Treeselect
                  v-model="directive_doc"
                  class="treeselect-noborder treeselect-wide"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="directive_docs_select"
                  placeholder="Исполнитель не выбран"
                  :append-to-body="true"
                  :clearable="false"
                />
              </td>
            </tr>
            <tr v-if="selected_card.medbookNumber || l2_harmful_factor">
              <td class="table-header-row">
                Мед.книжка:
              </td>
              <td
                class="table-content-row"
              >
                <strong>{{ selected_card.medbookNumber }}</strong>
              </td>
              <td
                class="cl-td"
                colspan="2"
              >
                <button
                  v-tippy="{ placement: 'bottom', arrow: true }"
                  class="btn last btn-blue-nb nbr"
                  style="height: 31px; float: right"
                  type="button"
                  title="Факторы вредности"
                  @click="open_harmful_factor()"
                >
                  <i class="fa fa-bolt" />
                </button>
              </td>
            </tr>
            <tr v-if="!hasSnils">
              <td
                class="table-content-row error-row"
                colspan="4"
              >
                <strong>Некорректный СНИЛС!</strong>
              </td>
            </tr>
          </tbody>
        </table>
        <div
          v-if="phones.length > 0 && !hide_card_editor"
          class="hovershow"
        >
          <div class="fastlinks hovershow1">
            <a href="#"><i class="glyphicon glyphicon-phone" /> Позвонить</a>
          </div>
          <div
            class="fastlinks hovershow2"
            style="margin-top: 1px"
          >
            <a
              v-for="p in phones"
              :key="p"
              :href="'sip:' + p"
              style="display: inline-block"
            >
              <i class="glyphicon glyphicon-phone" /> {{ format_number(p) }}
            </a>
          </div>
        </div>
        <div v-if="phones_tranfer.length > 0">
          <Treeselect
            v-model="current_transfer"
            :multiple="false"
            :disable-branch-nodes="true"
            :options="phones_tranfer"
            placeholder="Выбрать куда позвонить"
          />
          <div
            v-if="current_transfer > 0 && !hide_card_editor"
            class="hovershow"
          >
            <div class="fastlinks hovershow1">
              <a href="#"><i class="glyphicon glyphicon-phone" /> Звонок</a>
            </div>
            <div
              class="fastlinks hovershow2"
              style="margin-top: 1px"
            >
              <a
                :href="'sip:' + current_transfer"
                style="display: inline-block"
              >
                <i class="glyphicon glyphicon-phone" /> {{ current_transfer }}
              </a>
            </div>
          </div>
        </div>
        <div
          v-if="extrenal_phones.length > 0 && !hide_card_editor"
          class="hovershow call-padding-top"
        >
          <h5>Экстренные службы</h5>
          <div
            style="margin-top: 2px"
            class="fastlinks"
          >
            <a
              v-for="p in extrenal_phones"
              :key="p.id"
              :href="'sip:' + p.id"
              style="display: inline-block"
              class="call-padding-right"
            >
              <i class="glyphicon glyphicon-phone" /> {{ p.label }}
            </a>
          </div>
        </div>

        <slot
          v-if="loaded"
          name="for_card"
          style="margin-top: 5px"
        />
        <slot
          name="for_all"
          style="margin-top: 5px"
        />
      </div>
    </div>
    <div
      v-if="bottom_picker === 'true'"
      class="bottom-picker"
    >
      <slot name="for_card_bottom" />
    </div>
    <Modal
      v-if="showModal"
      ref="modal"
      show-footer="true"
      @close="hide_modal"
    >
      <span slot="header">Найдено несколько карт</span>
      <div slot="body">
        <div
          v-for="(row, i) in founded_cards"
          :key="row.pk"
          class="founded"
          @click="select_card(i)"
        >
          <div class="founded-row">
            Карта <span class="b">{{ row.type_title }} {{ row.num }}</span>
          </div>
          <div class="founded-row">
            <span class="b">ФИО, пол:</span> {{ row.family }} {{ row.name }} {{ row.twoname }}, {{ row.sex }}
          </div>
          <div class="founded-row">
            <span class="b">Дата рождения:</span> {{ row.birthday }} ({{ row.age }})
          </div>
          <div
            v-for="d in row.docs"
            :key="d.pk"
            class="founded-row"
          >
            <span class="b">{{ d.type_title }}:</span> {{ d.serial }} {{ d.number }}
          </div>
        </div>
      </div>
      <div
        slot="footer"
        class="text-center"
      >
        <small>Показано не более 10 карт</small>
      </div>
    </Modal>
    <L2CardCreate
      v-if="editor_pk !== -2"
      :card_pk="editor_pk"
      :base_pk="base"
    />
    <DReg
      v-if="dreg"
      :card_pk="selected_card.pk"
      :card_data="selected_card"
      :selected-researches="selectedResearches"
    />
    <Vaccine
      v-if="vaccine"
      :card_pk="selected_card.pk"
      :card_data="selected_card"
    />
    <Benefit
      v-if="benefit"
      :card_pk="selected_card.pk"
      :card_data="selected_card"
      :readonly="false"
    />
    <HarmfulFactor
      v-if="harmful_factor"
      :card_pk="selected_card.pk"
      :card_data="selected_card"
      :readonly="false"
    />
    <AmbulatoryData
      v-if="ambulatory_data && selected_card.pk"
      :card_pk="selected_card.pk"
      :card_data="selected_card"
    />
    <Modal
      v-if="anamnesis"
      ref="modalAnamnesis"
      show-footer="true"
      white-bg="true"
      max-width="710px"
      width="100%"
      margin-left-right="auto"
      margin-top
      class="an"
      @close="hide_modal_anamnesis"
    >
      <span slot="header">Анамнез жизни – карта {{ selected_card.num }}, {{ selected_card.fio_age }}</span>
      <div
        slot="body"
        class="an-body"
      >
        <div class="an-sidebar">
          <div
            class="an-s"
            :class="{ active: an_state.tab === 'text' }"
            @click="an_tab('text')"
          >
            Анамнез
          </div>
          <div
            class="an-s"
            :class="{ active: an_state.tab === 'history' }"
            @click="an_tab('history')"
          >
            История изменений
          </div>
        </div>
        <div class="an-content">
          <div v-if="an_state.tab === 'text'">
            <pre>{{ anamnesis_data.text || 'нет данных' }}</pre>
          </div>
          <div
            v-else
            class="an-history"
          >
            <div
              v-for="h in anamnesis_data.history"
              :key="h.pk"
            >
              <pre>{{ h.text || 'нет данных' }}</pre>
              {{ h.who_save.fio }}, {{ h.who_save.department }}. {{ h.datetime }}
            </div>
          </div>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="hide_modal_anamnesis"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import { mapGetters } from 'vuex';
import { debounce } from 'lodash';

import Modal from '@/ui-cards/Modal.vue';
import L2CardCreate from '@/modals/L2CardCreate.vue';
import DReg from '@/modals/DReg.vue';
import Benefit from '@/modals/Benefit.vue';
import HarmfulFactor from '@/modals/HarmfulFactor.vue';
import * as actions from '@/store/action-types';
import patientsPoint from '@/api/patients-point';
import Vaccine from '@/modals/Vaccine.vue';
import AmbulatoryData from '@/modals/AmbulatoryData.vue';

const tfomsRe = /^([А-яЁё-]+) ([А-яЁё-]+)( ([А-яЁё-]+))? (([0-9]{2})\.?([0-9]{2})\.?([0-9]{4}))$/;

export default {
  name: 'PatientPicker',
  components: {
    Vaccine,
    Treeselect,
    Modal,
    L2CardCreate,
    DReg,
    Benefit,
    HarmfulFactor,
    AmbulatoryData,
  },
  props: {
    directive_from_need: {
      default: 'false',
      type: String,
    },
    search_results: {
      default: 'false',
      type: String,
    },
    bottom_picker: {
      default: 'false',
      type: String,
    },
    history_n: {
      default: 'true',
      type: String,
    },
    hide_card_editor: {
      type: Boolean,
      default: false,
    },
    value: {},
    selectedResearches: {
      type: Array,
      required: false,
    },
  },
  data() {
    return {
      base: -1,
      query: '',
      directive_department: -1,
      directive_doc: -1,
      ofname_to_set: -1,
      ofname_to_set_dep: -1,
      local_directive_departments: [],
      directive_departments_select: [],
      showModal: false,
      founded_cards: [],
      selected_card: {},
      loaded: false,
      history_num: '',
      search_after_loading: false,
      open_edit_after_loading: false,
      editor_pk: -2,
      inc_rmis: false,
      inc_tfoms: false,
      anamnesis: false,
      ambulatory_data: false,
      anamnesis_data: {},
      an_state: {
        tab: 'text',
      },
      dreg: false,
      benefit: false,
      harmful_factor: false,
      template_editor: false,
      vaccine: false,
      suggests: {
        focused: -1,
        open: false,
        loading: false,
        data: [],
      },
      phones_tranfer: [],
      current_transfer: -1,
      extrenal_phones: [],
      current_extrenal_phones: -1,
    };
  },
  computed: {
    system() {
      return this.$systemTitle();
    },
    bases() {
      return this.$store.getters.bases.filter((b) => !b.hide);
    },
    basesFiltered() {
      return this.$store.getters.bases.filter((row) => !row.hide && row.pk !== this.selected_base.pk);
    },
    selected_base() {
      for (const b of this.bases) {
        if (b.pk === this.base) {
          return b;
        }
      }
      return {
        title: 'Не выбрана база',
        pk: -1,
        hide: false,
        history_number: false,
        fin_sources: [],
        internal_type: false,
      };
    },
    normalized_query() {
      return this.fixedQuery.trim();
    },
    tfoms_query() {
      return this.selected_base.internal_type && this.l2_tfoms && this.normalized_query.match(tfomsRe);
    },
    query_valid() {
      return this.normalized_query.length > 0;
    },
    l2_cards() {
      return this.$store.getters.modules.l2_cards_module;
    },
    l2_tfoms() {
      return this.$store.getters.modules.l2_tfoms;
    },
    l2_benefit() {
      return this.$store.getters.modules.l2_benefit;
    },
    l2_harmful_factor() {
      return this.$store.getters.modules.l2_harmful_factor;
    },
    force_rmis_search() {
      return Boolean(this.$store.getters.modules.l2_force_rmis_search);
    },
    tfoms_as_l2() {
      return Boolean(this.$store.getters.modules.l2_tfoms_as_l2);
    },
    auto_clinical_examination_direct() {
      return Boolean(this.$store.getters.modules.auto_clinical_examination_direct);
    },
    is_operator() {
      if ('groups' in this.$store.getters.user_data) {
        for (const g of this.$store.getters.user_data.groups) {
          if (g === 'Оператор лечащего врача') {
            return true;
          }
        }
      }
      return false;
    },
    is_doc() {
      if ('groups' in this.$store.getters.user_data) {
        for (const g of this.$store.getters.user_data.groups) {
          if (g === 'Лечащий врач') {
            return true;
          }
        }
      }
      return false;
    },
    is_l2_cards() {
      if ('groups' in this.$store.getters.user_data) {
        for (const g of this.$store.getters.user_data.groups) {
          if (
            g === 'Картотека'
            || g === 'Картотека L2'
            || g === 'Admin'
            || g === 'Лечащий врач'
            || g === 'Оператор лечащего врача'
          ) {
            return true;
          }
        }
      }
      return false;
    },
    l2_vaccine() {
      return this.$store.getters.modules.l2_vaccine;
    },
    directive_from_departments() {
      const r = {};
      for (const dep of this.local_directive_departments) {
        r[dep.pk] = dep;
      }
      return r;
    },
    directive_docs_select() {
      let o = [];
      if (this.directive_from_departments[this.directive_department]) {
        for (const d of this.directive_from_departments[this.directive_department].docs) {
          o.push({ label: d.fio, id: d.pk });
        }
      }
      if (!this.is_doc && o.length > 0) {
        o = [{ label: 'Выберите врача', id: -2 }, ...o];
      }
      return o;
    },
    inLoading() {
      return this.$store.getters.inLoading;
    },
    phones() {
      if ('phones' in this.selected_card) {
        return this.selected_card.phones;
      }
      return [];
    },
    hasSnils() {
      if (!this.selected_card.docs) {
        return true;
      }

      return this.selected_card.docs.some((d) => d.type_title === 'СНИЛС' && d.number && d.number.length >= 11);
    },
    ...mapGetters(['user_data']),
    allow_l2_card_edit() {
      return this.user_data.su || this.user_data.groups.includes('Картотека') || this.user_data.groups.includes('Картотека L2');
    },
    fixedQuery() {
      return this.query
        .split(' ')
        .map((s) => s
          .split('-')
          .map((x) => x.charAt(0).toUpperCase() + x.substring(1).toLowerCase())
          .join('-'))
        .join(' ');
    },
  },
  watch: {
    force_rmis_search: {
      handler() {
        this.inc_rmis = this.force_rmis_search;
      },
      immediate: true,
    },
    normalized_query() {
      this.keypress_other({ keyCode: -1 });
    },
    bases() {
      this.check_base();
    },
    directive_department() {
      this.update_ofname(this.directive_department !== -1);
    },
    directive_doc() {
      this.emit_input();
    },
    is_operator() {
      this.emit_input();
    },
    history_num() {
      this.emit_input(true);
    },
    inLoading() {
      if (!this.inLoading && (this.directive_department === -1 || this.directive_doc === -1)) {
        this.update_ofname();
      }
      if (!this.inLoading && this.search_after_loading) {
        this.search();
      }
    },
    tfoms_query(nv) {
      if (nv) {
        this.inc_tfoms = true;
      }
    },
    base: {
      immediate: true,
      handler() {
        this.$root.$emit('global:select-base', this.base);
        window.localStorage.setItem('selected-base', this.base);
      },
    },
  },
  created() {
    this.$store.watch(
      (state) => state.bases,
      () => {
        this.check_base();
      },
      { immediate: true },
    );
    this.$root.$on('search', () => {
      this.search();
    });
    this.$root.$on('search-value', (value) => {
      this.query = value;
      this.search();
    });
    this.$root.$on('select_card', (data) => {
      this.base = data.base_pk;
      this.query = `card_pk:${data.card_pk}:${data.inc_archive || false}`;
      this.search_after_loading = true;
      window.$(this.$refs.q).focus();
      this.emit_input();
      if (!data.hide) {
        this.editor_pk = data.card_pk;
      } else {
        this.editor_pk = -2;
      }
      setTimeout(() => {
        this.search();
        if (!data.hide) {
          setTimeout(() => {
            this.$root.$emit('reload_editor');
          }, 5);
        }
      }, 5);
    });
    this.$root.$on('hide_l2_card_create', () => {
      this.editor_pk = -2;
    });
    this.$root.$on('hide_dreg', () => {
      this.dreg = false;
    });
    this.$root.$on('hide_benefit', () => {
      this.benefit = false;
    });
    this.$root.$on('hide_harmful_factor', () => {
      this.harmful_factor = false;
    });
    this.$root.$on('hide_template_editor', () => {
      this.template_editor = false;
    });
    this.$root.$on('hide_vaccine', () => {
      this.vaccine = false;
    });
    this.$root.$on('hide_ambulatory_data', () => {
      this.ambulatory_data = false;
    });
  },
  mounted() {
    this.inited();
    this.get_phones_transfer();
  },
  methods: {
    fixQuery() {
      this.query = this.fixedQuery;
    },
    keypress(e) {
      if (!this.keypress_arrow(e)) {
        this.keypress_other(e);
      }
    },
    keypress_arrow(e) {
      if (e.keyCode === 38) {
        this.move_focus(-1);
        e.preventDefault();
        e.stopPropagation();
        e.cancelBubble = true;
        return true;
      }
      if (e.keyCode === 40) {
        this.move_focus(1);
        e.preventDefault();
        e.stopPropagation();
        e.cancelBubble = true;
        return true;
      }
      return false;
    },
    keypress_other: debounce(function (e) {
      if (e.keyCode !== 27 && e.keyCode !== 13) {
        this.loadSuggests();
      }
    }, 200),
    blur() {
      this.fixQuery();
      setTimeout(() => {
        this.suggests.open = false;
      }, 200);
    },
    suggests_focus() {
      if (this.normalized_query.length === 0) {
        return;
      }
      this.suggests.focused = -1;
      this.suggests.open = true;
      if (this.selected_card.pk) {
        this.$refs.q.setSelectionRange(0, this.query.length);
      }
    },
    move_focus(d) {
      this.suggests.focused += d;
      if (this.suggests.focused < -1) {
        this.suggests.focused = this.suggests.data.length - 1;
      } else if (this.suggests.focused > this.suggests.data.length - 1) {
        this.suggests.focused = -1;
      }
    },
    async loadSuggests() {
      if (this.normalized_query.length === 0) {
        this.suggests.open = false;
        this.suggests.loading = false;
        this.suggests.data = [];
        return;
      }
      this.suggests.loading = true;
      this.suggests.open = true;

      this.suggests.data = (
        await patientsPoint.searchCard({
          type: this.base,
          query: this.normalized_query,
          list_all_cards: false,
          inc_rmis: false,
          inc_tfoms: false,
          suggests: true,
        })
      ).results;

      if (this.suggests.data.length === 0) {
        this.suggests.focused = -1;
      }

      this.move_focus(0);

      this.suggests.loading = false;
    },
    select_suggest(i) {
      this.founded_cards = this.suggests.data;
      window.$('input').each(function () {
        window.$(this).trigger('blur');
      });
      this.select_card(i);
    },
    clear_input() {
      this.query = '';
      window.$(this.$refs.q).focus();
    },
    click_input() {
      this.loadSuggests();
    },
    async inited() {
      await this.$store.dispatch(actions.INC_LOADING);
      // eslint-disable-next-line no-constant-condition
      while (true) {
        if (!this.$store.getters.user_data.loading) {
          break;
        }
        await new Promise((r) => {
          setTimeout(r, 10);
        });
      }
      await this.$store.dispatch(actions.GET_DIRECTIVE_FROM);
      await this.$store.dispatch(actions.DEC_LOADING);

      this.local_directive_departments = this.$store.getters.directive_from;
      this.directive_departments_select = [];
      for (const dep of this.local_directive_departments) {
        this.directive_departments_select.push({ label: dep.title, id: dep.pk });
      }

      if (this.$store.getters.user_data?.department && this.local_directive_departments.length > 0 && this.ofname_to_set === -1) {
        for (const dep of this.local_directive_departments) {
          if (dep.pk === this.$store.getters.user_data.department.pk) {
            this.directive_department = dep.pk;
            this.check_base();
            return;
          }
        }
        this.directive_department = this.local_directive_departments[0].pk;
      }

      this.check_base();
    },
    open_anamnesis() {
      this.$store.dispatch(actions.INC_LOADING);
      patientsPoint
        .loadAnamnesis({ card_pk: this.selected_card.pk })
        .then((data) => {
          this.an_tab('text');
          this.anamnesis_data = data;
        })
        .finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
          this.anamnesis = true;
        });
    },
    hide_modal_anamnesis() {
      if (this.$refs.modalAnamnesis) {
        this.$refs.modalAnamnesis.$el.style.display = 'none';
      }
      this.anamnesis_data = {};
      this.anamnesis = false;
    },
    an_tab(tab) {
      this.an_state.tab = tab;
    },
    open_dreg() {
      this.dreg = true;
    },
    open_vaccine() {
      this.vaccine = true;
    },
    open_benefit() {
      this.benefit = true;
    },
    open_harmful_factor() {
      this.harmful_factor = true;
    },
    open_ambulatory_data() {
      this.ambulatory_data = true;
    },
    open_editor(isnew) {
      if (isnew) {
        this.editor_pk = -1;
      } else {
        this.editor_pk = this.selected_card.pk;
      }
    },
    format_number(a) {
      if (a.length === 6) {
        return `${a.slice(0, 2)}-${a.slice(2, 4)}-${a.slice(4, 6)}`;
      }
      if (a.length === 11) {
        if (a.charAt(1) !== '9' && a.charAt(1) !== '8') {
          return `${a.slice(0, 1)}-${a.slice(1, 5)}-${a.slice(5, 7)}-${a.slice(7, 9)}-${a.slice(9, 11)}`;
        }
        return `${a.slice(0, 1)}-${a.slice(1, 4)}-${a.slice(4, 6)}-${a.slice(6, 8)}-${a.slice(8, 10)}-${a.slice(10, 11)}`;
      }
      return a;
    },
    hide_modal() {
      this.showModal = false;
      if (this.$refs.modal) this.$refs.modal.$el.style.display = 'none';
    },
    update_ofname(force) {
      if (this.ofname_to_set === -2 || (this.inLoading && !force)) return;
      if (this.ofname_to_set !== -1) {
        if (this.ofname_to_set_dep !== -1) {
          this.directive_department = this.ofname_to_set_dep;
          this.directive_doc = this.ofname_to_set;
          this.$root.$emit('resync');
          this.emit_input();
          this.ofname_to_set = -2;
          return;
        }
        const dps = Object.keys(this.directive_from_departments);
        if (dps.length > 0 && !this.inLoading) {
          const onts = this.ofname_to_set;
          this.ofname_to_set = -1;
          for (const d of dps) {
            const users = this.directive_from_departments[d].docs;
            for (const u of users) {
              if (Number(u.pk) === Number(onts)) {
                this.directive_department = Number(d);
                this.directive_doc = onts;
                this.emit_input();
                this.ofname_to_set = -2;
                return;
              }
            }
          }
        }
        return;
      }
      let dpk = -1;
      if (this.directive_department !== -1) {
        for (const d of this.directive_docs_select) {
          if (d.id === this.$store.getters.user_data.doc_pk) {
            dpk = d.id;
            break;
          }
        }
        if (dpk === -1 && this.directive_docs_select.length > 0) {
          dpk = this.directive_docs_select[0].id;
        }
      }
      this.directive_doc = dpk;
    },
    select_base(pk) {
      this.base = pk;
      this.emit_input();
      this.search();
    },
    select_card(index) {
      this.hide_modal();
      this.suggests.open = false;
      this.suggests.loading = false;
      this.suggests.data = [];
      this.selected_card = this.founded_cards[index];
      if (this.selected_card.base_pk) {
        if (this.base && this.base !== this.selected_card.base_pk) {
          this.query = '';
        }
        this.base = this.selected_card.base_pk;
      }
      setTimeout(() => {
        if (this.selected_card.status_disp === 'need' && this.$refs.disp) {
          window.$(this.$refs.disp).click();
        }
      }, 10);
      this.emit_input();
      this.loaded = true;
      this.$root.$emit('patient-picker:select_card');
      setTimeout(() => {
        if (!this.auto_clinical_examination_direct || !this.is_operator || !this.is_doc) {
          return;
        }
        const pks = this.selected_card.disp_data?.filter((d) => !d[2]).map((d) => d[0]) || [];
        if (pks.length === 0) {
          return;
        }
        this.add_researches(pks, true);
        this.$root.$emit('msg', 'ok', 'Добавлены назначения по диспансеризации');
      }, 100);
    },
    check_base() {
      if (this.base === -1 && this.bases.length > 0) {
        const params = new URLSearchParams(window.location.search);
        const rmisUid = params.get('rmis_uid');
        const basePk = params.get('base_pk');
        const cardPk = params.get('card_pk');
        const phone = params.get('phone');
        const openEdit = params.get('open_edit') === 'true';
        const ofname = params.get('ofname');
        const ofnameDep = params.get('ofname_dep');
        const q = params.get('q');

        if (rmisUid) {
          window.history.pushState('', '', window.location.href.split('?')[0]);
          let hasInternal = false;
          for (const row of this.bases) {
            if (row.internal_type) {
              this.base = row.pk;
              this.query = rmisUid;
              this.search_after_loading = true;
              hasInternal = true;
              break;
            }
          }
          if (!hasInternal) {
            for (const row of this.bases) {
              if (row.code === 'Р') {
                this.base = row.pk;
                this.query = rmisUid;
                this.search_after_loading = true;
                break;
              }
            }
          }
          if (this.base === -1) {
            this.base = this.bases[0].pk;
          }
        } else if (basePk) {
          window.history.pushState('', '', window.location.href.split('?')[0]);
          if (ofname) {
            this.ofname_to_set = ofname;
          }
          if (ofnameDep) {
            this.ofname_to_set_dep = ofnameDep;
          }
          for (const row of this.bases) {
            if (row.pk === parseInt(basePk, 10)) {
              this.base = row.pk;
              break;
            }
          }
          if (this.base === -1) {
            this.base = this.bases[0].pk;
          }
          if (cardPk) {
            this.query = `card_pk:${cardPk}`;
            this.search_after_loading = true;
            this.open_edit_after_loading = openEdit;
          }
        } else if (q) {
          window.history.pushState('', '', window.location.href.split('?')[0]);

          for (const b of this.bases) {
            if (b.internal_type) {
              this.base = b.pk;
              break;
            }
          }

          if (this.base === -1) {
            this.base = this.bases[0].pk;
          }
          this.query = q;
          this.search_after_loading = true;
        } else {
          this.base = this.bases[0].pk;
        }
        if (phone) {
          window.history.pushState('', '', window.location.href.split('?')[0]);
          this.query = `phone:${phone}`;
          this.search_after_loading = true;
          this.open_edit_after_loading = openEdit;
        }
        this.emit_input();
        setTimeout(() => window.$(this.$refs.q).focus(), 200);
      }
    },
    emit_input(fromHn = false) {
      let pk = -1;
      if ('pk' in this.selected_card) pk = this.selected_card.pk;
      let individualPk = -1;
      if ('individual_pk' in this.selected_card) individualPk = this.selected_card.individual_pk;
      this.$emit('input', {
        pk,
        individual_pk: individualPk,
        base: this.selected_base,
        ofname_dep: parseInt(this.directive_department, 10),
        ofname: parseInt(this.directive_doc, 10),
        operator: this.is_operator,
        history_num: this.history_num,
        is_rmis: this.selected_card.is_rmis,
        family: this.selected_card.family,
        name: this.selected_card.name,
        twoname: this.selected_card.twoname,
        birthday: this.selected_card.birthday,
        age: this.selected_card.age,
        main_diagnosis: this.selected_card.main_diagnosis,
        isArchive: this.selected_card.isArchive,
      });
      if (pk !== -1 && !fromHn) {
        window.$('#fndsrc').focus();
      }
    },
    clear() {
      this.loaded = false;
      this.selected_card = {};
      this.history_num = '';
      this.founded_cards = [];
      if (this.query.toLowerCase().includes('card_pk:') || this.query.toLowerCase().includes('phone:')) {
        this.query = '';
      }
      this.emit_input();
    },
    open_as_l2_card() {
      this.$store.dispatch(actions.ENABLE_LOADING, { loadingLabel: 'Загрузка' });
      patientsPoint
        .searchL2Card({ card_pk: this.selected_card.pk })
        .then((result) => {
          this.clear();
          if (result.results) {
            this.founded_cards = result.results;
            if (this.founded_cards.length > 1) {
              this.showModal = true;
            } else if (this.founded_cards.length === 1) {
              this.select_card(0);
            }
          } else {
            this.$root.$emit('msg', 'error', 'Ошибка на сервере');
          }
        })
        .catch((error) => {
          this.$root.$emit('msg', 'error', `Ошибка на сервере\n${error.message}`);
        })
        .finally(() => {
          this.$store.dispatch(actions.DISABLE_LOADING);
        });
    },
    search(args) {
      const source = args?.source || 'js';
      if (!this.query_valid || this.inLoading) return;
      this.suggests.open = false;
      this.suggests.loading = false;
      if (this.suggests.focused > -1 && this.suggests.data.length > 0 && source !== 'button') {
        this.select_suggest(this.suggests.focused);
        return;
      }
      this.suggests.data = [];
      const q = this.query;
      this.check_base();
      window.$('input').each(function () {
        window.$(this).trigger('blur');
      });
      this.$store.dispatch(actions.ENABLE_LOADING, { loadingLabel: 'Поиск карты' });
      patientsPoint
        .searchCard({
          type: this.base,
          query: q,
          list_all_cards: false,
          inc_rmis: this.inc_rmis || this.search_after_loading,
          inc_tfoms: this.inc_tfoms && this.tfoms_query,
        })
        .then((result) => {
          this.clear();
          if (result.results) {
            this.founded_cards = result.results;
            if (this.founded_cards.length > 1) {
              this.showModal = true;
            } else if (this.founded_cards.length === 1) {
              this.select_card(0);
              if (this.open_edit_after_loading) {
                this.open_editor();
              }
            } else {
              this.$root.$emit('msg', 'error', 'Карт по такому запросу не найдено');
            }
          } else {
            this.$root.$emit('msg', 'error', 'Ошибка на сервере');
          }
          if (this.search_after_loading) {
            this.search_after_loading = false;
            this.query = '';
          }
        })
        .catch((error) => {
          this.$root.$emit('msg', 'error', `Ошибка на сервере\n${error.message}`);
        })
        .finally(() => {
          this.open_edit_after_loading = false;
          this.$store.dispatch(actions.DISABLE_LOADING);
        });
    },
    add_researches(pks, full = false) {
      for (const pk of pks) {
        this.$root.$emit('researches-picker:add_research', pk);
      }
      if (full) {
        if (this.$refs.disp) {
          window.$(this.$refs.disp).click();
          window.$(this.$refs.disp).blur();
        }
      }
    },
    show_results(pk) {
      this.$root.$emit('print:results', pk);
    },

    async get_phones_transfer() {
      const rows = await this.$api('external-system/phones-transfers');
      this.phones_tranfer = rows.org_phones;
      this.extrenal_phones = rows.extrenal_phones;
    },
  },
};
</script>

<style scoped lang="scss">
table {
  table-layout: fixed;
  padding: 0;
  margin: 5px 0 0;
}

td:not(.select-td):not(.cl-td) {
  padding: 2px !important;
}

.table-header-row {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
}

.table-content-row:not(.cl-td) {
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
}

.content-picker {
  position: absolute;
  top: 34px;
  left: 0;
  right: 0;
  bottom: 34px;
  overflow-y: auto;
  overflow-x: hidden;
}

.top-picker,
.bottom-picker {
  height: 34px;
  background-color: #aab2bd;
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  white-space: nowrap;
}

.bottom-picker {
  bottom: 0;
}

.top-picker {
  top: 0;
}

.bottom-inner {
  display: flex;
  flex-wrap: wrap;
  flex-direction: row;
  justify-content: flex-end;
  align-items: stretch;
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  height: 34px;
  align-content: stretch;

  a:not(.ddm) {
    align-self: stretch;
    display: flex;
    align-items: center;
    padding: 1px 2px 1px;
    text-decoration: none;
    transition: 0.15s linear all;
    cursor: pointer;
    flex: 1;
    margin: 0;
    font-size: 12px;
    min-width: 0;
    max-width: 150px;
    background-color: #aab2bd;
    color: #fff;
    text-align: right;
    justify-content: center;

    span {
      display: block;
      text-overflow: ellipsis;
      overflow: hidden;
      word-break: keep-all;
      max-height: 2.2em;
      line-height: 1.1em;
    }

    &:hover {
      background-color: #434a54;
    }
  }
}

.dropdown-menu {
  max-width: 350px;
  min-width: 1%;
}
</style>

<style lang="scss">
.call-padding-right {
  padding-right: 15px;
}

.call-padding-top {
  padding-top: 20px;
}

.select-td {
  padding: 0 !important;

  .bootstrap-select {
    height: 38px;
    display: flex !important;

    button {
      border: none !important;
      border-radius: 0 !important;

      .filter-option {
        text-overflow: ellipsis;
      }
    }
  }
}

.hovershow {
  position: relative;

  a {
    font-size: 12px;
  }

  .hovershow1 {
    top: 1px;
    position: absolute;

    a {
      color: grey;
      display: inline-block;
    }

    color: grey;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
  }

  .hovershow2 {
    opacity: 0;
  }

  &:hover {
    .hovershow1 {
      display: none;
    }

    .hovershow2 {
      opacity: 1;
      transition: 0.5s ease-in opacity;
    }
  }
}

.bob {
  border-left: none !important;
  border-top: none !important;
  border-right: none !important;
}

.internal_type {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;

  .btn {
    align-self: stretch;
    flex: 1;
    padding: 6px 0;
  }
}

.founded {
  background: #fff;
  margin-bottom: 10px;
  cursor: pointer;
  padding: 5px;
  border-radius: 5px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;

  &:hover {
    transform: scale(1.03);
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
    z-index: 1;
  }
}

.b {
  font-weight: bold;
}

.hospital input {
  border-radius: 0;
}

.dsp {
  a:not(.btn):not(.not-black) {
    color: #0d0d0d !important;
    text-decoration: dotted underline;

    &:hover {
      text-decoration: none;
    }
  }

  &_need,
  &_need:focus,
  &_need:active,
  &_need:hover {
    background: #f4d03f !important;
  }

  &_finished,
  &_finished:focus,
  &_finished:active,
  &_finished:hover {
    background: #049372 !important;
  }

  .btn {
    width: 100%;
    padding: 4px;
  }

  &_row {
    font-weight: bold;
    display: inline-block;
    width: 76px;

    &_need,
    &_need a {
      color: #ff0000 !important;
    }

    &_finished,
    &_finished a {
      color: #049372 !important;
    }

    a {
      text-decoration: dotted underline;

      &:hover {
        text-decoration: none;
      }
    }
  }
}

.base-toggle {
  max-width: 200px;
  min-width: 60px;
  text-align: left !important;
}

.autocomplete {
  position: relative;
  overflow: visible;
  height: 34px;

  input {
    border-radius: 0;
  }

  .suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #fff;
    border-radius: 0 0 5px 5px;
    border: 1px solid #3bafda;
    border-top: none;
    box-shadow: 0 10px 20px rgba(#3bafda, 0.19), 0 6px 6px rgba(#3bafda, 0.23);
    overflow: hidden;
    z-index: 1000;

    .item {
      padding: 3px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      word-break: keep-all;

      &-doc {
        color: #888;
        font-size: 85%;
      }

      &-selectable {
        cursor: pointer;
        &-focused {
          background: rgba(#3bafda, 0.1);
        }
      }
    }
  }

  .clear-input {
    display: none;
    position: absolute;
    cursor: pointer;
    top: 0;
    right: 0;
    width: 34px;
    height: 34px;
    opacity: 0.6;

    &:hover {
      background: rgba(0, 0, 0, 0.15);
      opacity: 1;
    }

    &.display {
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 10;
    }
  }
}

.error-row {
  color: #f00;
}
</style>
