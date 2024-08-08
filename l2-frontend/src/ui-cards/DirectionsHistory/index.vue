<template>
  <div
    style="height: 100%;width: 100%;position: relative"
    :class="[!!iss_pk && 'no_abs']"
  >
    <div
      v-if="!iss_pk"
      class="top-picker"
    >
      <div
        v-tippy="{ placement: 'right', arrow: true }"
        class="direct-date"
        title="Дата направления"
      >
        <DateRange
          v-model="date_range"
          small
        />
      </div>
      <div class="top-inner">
        <div class="top-select">
          <SelectPickerM
            v-model="services"
            :options="services_options"
            actions_box
            multiple
            none-text="Все услуги"
            search
            uid="services_options"
          />
        </div>
        <div class="position-relative">
          <button
            class="btn btn-blue-nb btn-ell dropdown-toggle nbr"
            data-toggle="dropdown"
            style="text-align: left!important;width: 100%;"
            type="button"
          >
            <span
              v-if="typesFiltered.length > 0"
              class="caret"
            /> {{ active_type_obj.title }}
          </button>
          <ul
            v-if="typesFiltered.length > 0"
            class="dropdown-menu"
          >
            <li
              v-for="row in typesFiltered"
              :key="row.pk"
            >
              <a
                :title="row.title"
                href="#"
                @click.prevent="select_type(row.pk)"
              >
                {{ row.title }}
              </a>
            </li>
          </ul>
        </div>
        <button
          v-if="modules.showBarcodeButtonInDirectionHistory"
          v-tippy
          class="btn btn-blue-nb btn-ell nbr"
          title="Акт"
          @click="printAct"
        >
          <i class="fa-regular fa-file-lines" />
        </button>
        <button
          v-tippy
          class="btn btn-blue-nb btn-ell nbr"
          title="Обновить"
          @click="load_history_safe_fast"
        >
          <i class="glyphicon glyphicon-refresh" />
        </button>
        <button
          v-if="modules.showBarcodeButtonInDirectionHistory && checked.length > 0"
          v-tippy
          class="btn btn-blue-nb btn-ell nbr"
          title="Ш/К"
          @click="printBarcodes"
        >
          <i class="fa fa-barcode" />
        </button>
      </div>
    </div>
    <div class="content-picker">
      <table class="table table-responsive table-bordered table-one">
        <colgroup>
          <col width="66">
          <col width="77">
          <col>
          <col width="65">
          <col :width="!!iss_pk ? 200 : 150">
          <col width="28">
        </colgroup>
        <thead>
          <tr>
            <th class="text-center">
              Дата
            </th>
            <th v-if="active_type === 7">
              № случ.
            </th>
            <th v-else-if="active_type === 8">
              № компл.
            </th>
            <th v-else-if="active_type !== 5 && active_type !== 6">
              № напр.
            </th>
            <th v-else-if="active_type === 5">
              № дог
            </th>
            <th v-else>
              Время
            </th>
            <th>Назначения</th>
            <th
              v-if="active_type !== 5"
              class="text-center"
            >
              Статус
            </th>
            <th
              v-else
              class="text-center"
            >
              Сумма
            </th>
            <th />
            <th class="nopd noel">
              <input
                v-model="all_checked"
                type="checkbox"
              >
            </th>
          </tr>
        </thead>
      </table>
      <table class="table table-responsive table-bordered no-first-border-top table-hover table-two">
        <colgroup>
          <col width="66">
          <col width="77">
          <col>
          <col width="65">
          <col :width="!!iss_pk ? 200 : 150">
          <col width="28">
        </colgroup>
        <tbody>
          <tr v-if="directions.length === 0 && is_created">
            <td
              class="text-center"
              :colspan="6"
            >
              Не найдено
            </td>
          </tr>
          <tr v-if="directions.length === 0 && !is_created">
            <td
              class="text-center"
              :colspan="6"
            >
              Загрузка...
            </td>
          </tr>
          <tr
            v-for="row in directions"
            :key="row.pk"
          >
            <td class="text-center">
              {{ row.date }}
            </td>
            <td>
              <span v-if="!!row.has_hosp && role_can_use_stationar">
                <!-- eslint-disable-next-line max-len -->
                <a
                  :href="stationar_link(row.pk)"
                  target="_blank"
                  class="a-under"
                >
                  {{ row.pk }}
                </a>
              </span>
              <span v-else-if="!!row.has_descriptive && role_can_use_descriptive">
                <a
                  :href="`/ui/results/descriptive#{%22pk%22:${row.pk}}`"
                  target="_blank"
                  class="a-under"
                >
                  {{ row.pk }}
                </a>
              </span>
              <span v-else-if="active_type === 7">
                <a
                  :href="`/ui/case-control#{%22pk%22:${row.pk}}`"
                  target="_blank"
                  class="a-under"
                >
                  {{ row.pk }}
                </a>
              </span>
              <span v-else>{{ row.pk }}</span>
              <span v-if="row.has_aux">
                <AuxResearch
                  :main-direction="row.pk"
                  :aux-research="row.aux_researches"
                />
              </span>
            </td>
            <td
              class="researches"
              :title="row.researches +
                (row.planed_doctor !== '' ? ' Назначен: ' + row.planed_doctor: '') +
                (row.register_number !== '' ? ' (' + row.register_number + ')': '')
              "
            >
              <span v-if="row.lab && !row.has_hosp && roleCanUseGetBipmaterial">
                <a
                  v-tippy
                  href="#"
                  title="Забор биоматериала"
                  @click.prevent="getTubes(row.pk)"
                >
                  <i
                    class="fa-solid fa-vial"
                    style="color: #6f6f72"
                  />
                </a>
              </span>
              {{ row.researches }}
            </td>
            <td
              v-tippy="{ placement: 'bottom', arrow: true }"
              class="text-center"
              :title="
                statuses[row.status === 1 && row.has_descriptive ? -2 : row.status] +
                  (row.maybe_onco ? '. Онкоподозрение' : '') +
                  (row.is_expertise
                    ? row.expertise_status > 0
                      ? ' (экспертиза БЕЗ замечаний)'
                      : ' (экспертза С замечаниями)'
                    : '') + (row.person_contract_pk > 0 ? ' (Договор-' + row.person_contract_pk +
                    ' (Направления: ' + row.person_contract_dirs + ')': '') +
                  (row.planed_doctor !== '' ? ' Назначен: ' + row.planed_doctor: '') +
                  (row.register_number !== '' ? ' (' + row.register_number + ')': '')
              "
              :class="['status-' + row.status]"
            >
              <strong>
                <span v-if="row.rmis_number">e</span>
                {{ row.status }}
                <span v-if="row.maybe_onco">*О</span>
                <span v-if="row.is_application">**З</span>
                <span
                  v-if="row.is_expertise"
                  :class="['status-' + row.expertise_status]"
                >-Э</span>
                <span
                  v-if="row.person_contract_pk > 0"
                  style="color: #0d0d0d"
                >&#8381;</span>
              </strong>
            </td>
            <td class="button-td">
              <div
                v-if="!row.is_application && active_type !== 5 && active_type !== 6 && active_type !== 8"
                class="button-td-inner"
                :class="[
                  {
                    has_pacs_stationar: !!row.pacs && (!!row.parent.parent_is_hosp || !!row.parent.parent_is_doc_refferal),
                  },
                  {
                    has_pacs:
                      ((!!row.pacs || !!row.can_has_pacs) && !row.parent.parent_is_hosp) ||
                      (!row.pacs && !!row.parent.parent_is_hosp) ||
                      (!row.pacs && !!row.parent.parent_is_doc_refferal),
                  },
                ]"
              >
                <a
                  v-if="!!row.pacs"
                  v-tippy
                  :href="row.pacs"
                  title="Снимок"
                  target="_blank"
                  class="btn btn-blue-nb"
                >
                  <i class="fa fa-camera" />
                </a>
                <a
                  v-if="row.can_has_pacs && !row.pacs"
                  v-tippy
                  href="#"
                  title="Запросить снимок"
                  target="_blank"
                  class="btn btn-blue-nb"
                  @click.prevent="serachDicom(row.pk)"
                >
                  <i class="fa fa-camera-rotate" />
                </a>
                <a
                  v-if="!!row.parent.parent_is_hosp"
                  v-tippy
                  href="#"
                  :title="`Принадлежит и/б: ${row.parent.pk}-${row.parent.parent_title}`"
                  class="btn btn-blue-nb"
                  @click.prevent="role_can_use_stationar ? show_stationar(row.parent.pk) : null"
                >
                  <i class="fa fa-bed" />
                </a>
                <a
                  v-if="!!row.parent.parent_is_doc_refferal"
                  v-tippy
                  href="#"
                  :title="`Создано в амбулаторном приеме: ${row.parent.pk}-${row.parent.parent_title}`"
                  class="btn btn-blue-nb"
                  :class="{ isDisabled: !row.parent.is_confirm }"
                  @click.prevent="row.parent.is_confirm ? show_results(row.parent) : null"
                >
                  <i class="fa fa-user-md" />
                </a>
                <button
                  v-if="row.has_hosp"
                  v-tippy
                  class="btn btn-blue-nb"
                  title="Штрих-код браслета"
                  @click="print_hosp(row.pk)"
                >
                  <i class="fa fa-barcode" /> браслета
                </button>
                <button
                  v-if="modules.showCancelButton && row.status <= 1 && !row.has_hosp"
                  class="btn btn-blue-nb"
                  @click="cancel_direction(row.pk)"
                >
                  Отмена
                </button>
                <button
                  v-if="!modules.showCancelButton && row.status <= 1 && !row.has_hosp"
                  class="btn btn-blue-nb"
                  @click="printCurrentBarcodes(row.pk)"
                >
                  Ш/к
                </button>
                <button
                  v-else-if="!row.has_hosp && row.status === 2"
                  class="btn btn-blue-nb"
                  @click="show_results(row)"
                >
                  Результаты
                </button>
                <button
                  class="btn btn-blue-nb"
                  @click="print_direction(row.pk)"
                >
                  Направление
                </button>
              </div>
              <div
                v-else-if="row.is_application"
                class="button-td-inner button-td-inner-single"
              >
                <button
                  class="btn btn-blue-nb"
                  @click="print_direction(row.pk)"
                >
                  Заявление
                </button>
              </div>
              <div
                v-else-if="active_type===5"
                class="button-td-inner button-td-inner-single"
              >
                <button
                  class="btn btn-blue-nb"
                  @click="print_contract(row.pk, patient_pk)"
                >
                  Договор
                </button>
              </div>
              <div
                v-else-if="active_type===8"
                class="button-td-inner"
              >
                <button
                  class="btn btn-blue-nb"
                  @click="show_results(row)"
                >
                  Результаты
                </button>
                <button
                  class="btn btn-blue-nb"
                  @click="print_direction_for_complex(row.pk)"
                >
                  Направления
                </button>
              </div>
              <div
                v-else-if="active_type===6"
                class="button-td-inner has_pacs"
              >
                <button
                  v-tippy
                  class="btn btn-blue-nb"
                  title="Удалить запись"
                  @click="cancel_talon(row.timeTable_id, patient_pk, row.rmis_location, row.type_slot)"
                >
                  Х
                </button>
                <button
                  class="btn btn-blue-nb"
                  @click="print_talon(row.pk, patient_pk, row.date, row.rmis_location, row.researches, 'P80',
                                      row.type_slot)"
                >
                  Талон-80
                </button>
                <button
                  class="btn btn-blue-nb"
                  @click="print_talon(row.pk, patient_pk, row.date, row.rmis_location, row.researches, 'A6',
                                      row.type_slot)"
                >
                  Талон-А6
                </button>
              </div>
            </td>
            <td class="nopd">
              <input
                v-model="row.checked"
                type="checkbox"
              >
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <Bottom
      v-show="checked.length > 0 || !iss_pk"
      class="bottom-picker"
      :checked="checked"
      :directions="directions"
      :iss_pk="iss_pk"
      :card_pk="patient_pk"
      :active_type="active_type"
      :kk="kk"
    />
  </div>
</template>

<script lang="ts">
import moment from 'moment';
import { mapGetters } from 'vuex';
import _ from 'lodash';

import { Research } from '@/types/research';
import AuxResearch from '@/ui-cards/AuxResearch.vue';
import directionsPoint from '@/api/directions-point';
import * as actions from '@/store/action-types';

import SelectPickerM from '../../fields/SelectPickerM.vue';
import DateRange from '../DateRange.vue';
import Bottom from './Bottom/index.vue';

function truncate(s, n, useWordBoundary) {
  if (!s) {
    return '';
  }
  if (s.length <= n) {
    return s;
  }
  const subString = s.substr(0, n - 1);
  return `${useWordBoundary ? subString.substr(0, subString.lastIndexOf(' ')) : subString}...`;
}

export default {
  name: 'DirectionsHistory',
  components: {
    SelectPickerM, DateRange, Bottom, AuxResearch,
  },
  props: {
    patient_pk: {
      type: Number,
      default: -1,
      required: false,
    },
    iss_pk: {
      type: [String, Number],
      default: null,
      required: false,
    },
    kk: {
      type: String,
      default: '',
    },
    forHospSlave: {
      type: Boolean,
      required: false,
      default: false,
    },
    onlyType: {
      type: Number,
      required: false,
      default: null,
    },
    daysSubtract: {
      type: Number,
      required: false,
      default: 90,
    },
  },
  data() {
    return {
      date_range: [
        moment()
          .subtract(this.daysSubtract, 'day')
          .format('DD.MM.YY'),
        moment().format('DD.MM.YY'),
      ],
      types: [
        { pk: 3, title: 'Направления пациента' },
        { pk: 0, title: 'Только выписанные' },
        { pk: 1, title: 'Материал в лаборатории' },
        { pk: 2, title: 'Результаты подтверждены' },
        { pk: 4, title: 'Созданы пользователем' },
        { pk: 5, title: 'Договоры пациента' },
        { pk: 6, title: 'Регистратура пациента', module: 'rmisQueue' },
        { pk: 7, title: 'Случаи пациента' },
        { pk: 8, title: 'Комплексы пациента' },
      ],
      active_type: this.onlyType || 3,
      checked_obj: {},
      is_created: false,
      directions: [],
      checked: [],
      services: [],
      services_options: [],
      all_checked: false,
      statuses: {
        '-2': 'Посещение зарегистрировано',
        '-1': 'Направление отменено',
        0: 'Направление только выписано',
        1: 'Материал в лаборатории',
        2: 'Результаты подтверждены',
      },
    };
  },
  computed: {
    typesFiltered() {
      return this.types.filter(
        t => t.pk !== this.active_type
          && (this.onlyType || !t.module || this.modules[t.module])
          && (!this.onlyType || this.onlyType === t.pk),
      );
    },
    role_can_use_stationar() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (g === 'Врач стационара') {
          return true;
        }
      }
      return false;
    },
    roleCanUseGetBipmaterial() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (g === 'Заборщик биоматериала') {
          return true;
        }
      }
      return false;
    },
    role_can_use_descriptive() {
      for (const g of this.$store.getters.user_data.groups || []) {
        if (['Врач консультаций', 'Врач параклиники', 'Свидетельство о смерти-доступ'].includes(g)) {
          return true;
        }
      }
      return false;
    },
    active_type_obj() {
      for (const row of this.types) {
        if (row.pk === this.active_type) {
          return row;
        }
      }
      return {};
    },
    ...mapGetters({
      researches: 'researches_obj',
    }),
    modules() {
      return {
        rmisQueue: this.$store.getters.modules.l2_rmis_queue,
        showBarcodeButtonInDirectionHistory: this.$store.getters.modules.l2_show_barcode_button_in_direction_history,
        showCancelButton: this.$store.getters.modules.show_cancel_button,
      };
    },
  },
  watch: {
    active_type() {
      this.load_history_debounced();
    },
    patient_pk() {
      this.load_history_debounced();
    },
    date_range() {
      this.load_history_debounced();
    },
    services() {
      this.load_history_debounced();
    },
    all_checked() {
      for (const row of this.directions) {
        row.checked = this.all_checked;
      }
    },
    directions: {
      handler() {
        this.checked = [];
        for (const row of this.directions) {
          if (row.checked) {
            this.checked.push(row.pk);
          }
        }
      },
      deep: true,
    },
    researches: {
      handler() {
        this.update_so(this.researches);
      },
      immediate: true,
    },
  },
  mounted() {
    this.is_created = true;
    if (this.onlyType !== 6) {
      this.load_history();
    } else {
      this.load_history_safe();
    }
    this.$root.$on(`researches-picker:directions_created${this.kk}`, () => this.load_history_debounced());
    this.$root.$on(`researches-picker:refresh${this.kk}`, this.load_history_safe_fast);
  },
  methods: {
    async serachDicom(pk) {
      const { url } = await this.$api('/search-dicom', { pk });
      if (url) {
        window.open(url, '_blank');
      } else {
        this.$root.$emit('msg', 'warning', 'Снимок не найден');
      }
    },
    print_contract(pk, card) {
      window.open(`/forms/pdf?type=102.02&card_pk=${card}&contract_id=${pk}`, '_blank');
    },
    print_talon(time, card, date, rmisLocation, researches, pageFormat, typeSlot) {
      // eslint-disable-next-line max-len
      window.open(`/forms/pdf?type=111.01&card_pk=${card}&rmis_location=${rmisLocation}&date=${date}&time=${time}&researches=${researches}&pageFormat=${pageFormat}&typeSlot=${typeSlot}`, '_blank');
    },
    load_history_safe() {
      this.load_history_debounced(true);
    },
    async cancel_talon(slotId, patentPk, rmisLocation, typeSlot) {
      try {
        await this.$dialog.confirm('Подтвердите удаление записи');
      } catch (e) {
        return;
      }
      const { result } = await this.$api('/ecp/cancel-slot', {
        slotId, patentPk, rmisLocation, typeSlot,
      });
      if (result) {
        this.$root.$emit('msg', 'ok', 'Запись отменена');
      } else {
        this.$root.$emit('msg', 'warning', 'Не удалось удалить запись');
      }
      this.load_history_safe();
    },
    async load_history_safe_fast() {
      await this.load_history(true);
    },
    update_so(researches: { [key: string]: Research }) {
      const s = Object.values(researches || {}).map((r: Research) => ({
        value: String(r.pk),
        label: truncate(r.full_title || r.title, 70, true),
      })).filter(({ value }) => !value.startsWith('template-'));
      if (s.length === 0) {
        return;
      }
      s.sort((a, b) => (a.label.toUpperCase() > b.label.toUpperCase() ? 1 : -1));
      this.services_options = s;
      setTimeout(() => {
        this.$root.$emit('update-sp-m-services_options');
      }, 0);
    },
    stationar_link(dir) {
      const path = `/ui/stationar#{%22pk%22:${dir},%22opened_list_key%22:null,%22opened_form_pk%22:null,%22every%22:false}`;
      return path;
    },
    show_stationar(dir) {
      window.open(this.stationar_link(dir), '_blank');
    },
    show_results(row) {
      if (row.has_descriptive) {
        this.$root.$emit('print:results', [row.pk]);
      } else if (row.isComplex) {
        this.$root.$emit('print:results', [row.pk], row.isComplex);
      } else {
        this.$root.$emit('show_results', row.pk);
      }
    },
    print_direction(pk) {
      this.$root.$emit('print:directions', [pk]);
    },
    print_direction_for_complex(pk) {
      this.$root.$emit('print:complex:directions', [pk]);
    },
    print_hosp(pk) {
      this.$root.$emit('print:hosp', [pk]);
    },
    async cancel_direction(pk) {
      await this.$store.dispatch(actions.INC_LOADING);

      const data = await directionsPoint.cancelDirection({ pk });
      if (data.forbidden) {
        this.$root.$emit('msg', 'warning', 'Недостаточно прав для отмены направлений');
      }

      for (const dir of this.directions) {
        if (dir.pk === pk) {
          dir.cancel = data.cancel;
          if (dir.status === -1 && !dir.cancel) {
            dir.status = 0;
          } else if (dir.status === 0 && dir.cancel) {
            dir.status = -1;
          }
          break;
        }
      }

      await this.$store.dispatch(actions.DEC_LOADING);
    },
    select_type(pk) {
      this.active_type = pk;
    },
    load_history_debounced: _.debounce(function (safe?: boolean) {
      this.load_history(safe);
    }, 300),
    async load_history(safe?: boolean) {
      if (!this.is_created) return;
      this.$root.$emit('validate-datepickers');
      this.is_created = false;

      await this.$store.dispatch(actions.INC_LOADING);
      this.directions = [];
      if (!safe) {
        this.all_checked = false;
      }

      const checked = [];

      if (safe) {
        checked.push(...this.checked);
      }

      await directionsPoint
        .getHistory(this, ['iss_pk', 'services', 'forHospSlave'], {
          type: this.active_type,
          patient: this.patient_pk,
          date_from: moment(this.date_range[0], 'DD.MM.YY').format('DD.MM.YYYY'),
          date_to: moment(this.date_range[1], 'DD.MM.YY').format('DD.MM.YYYY'),
        })
        .then(data => {
          this.directions = data.directions;
          for (const d of this.directions) {
            if (checked.includes(d.pk)) {
              d.checked = true;
            }
          }
        })
        .finally(() => {
          this.is_created = true;
          return this.$store.dispatch(actions.DEC_LOADING);
        });
    },
    in_checked(pk) {
      return this.checked.indexOf(pk) !== -1;
    },
    sync_check(pk, env) {
      const v = env.target.checked;
      if (!v) {
        this.checked = this.checked.filter(e => e !== pk);
      } else if (!this.in_checked(pk)) {
        this.checked.push(pk);
      }
    },
    printBarcodes() {
      this.$root.$emit('print:barcodes', this.checked);
    },
    printAct() {
      const dateStart = moment(this.date_range[0], 'DD.MM.YY').format('DD.MM.YYYY');
      window.open(`/forms/pdf?type=114.01&date=${dateStart}`, '_blank');
    },
    printCurrentBarcodes(pk) {
      this.$root.$emit('print:barcodes', [pk]);
    },
    getTubes(directionId) {
      window.open(`/ui/biomaterial/get#{%22pk%22:${directionId}}`, '_blank');
    },
  },
};
</script>

<style scoped lang="scss">
.isDisabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.top-picker,
.bottom-picker {
  height: 34px;
  background-color: #aab2bd;
  position: absolute;
  left: 0;
  right: 0;
}

.top-picker {
  top: 0;
  white-space: nowrap;

  ::v-deep {
    input {
      border-radius: 0;
      border: none;
      border-bottom: 1px solid #aab2bd;
      background: #fff;
    }

    .input-group-addon {
      border: 1px solid #aab2bd;
      border-top: none;
    }
  }
}

.content-picker,
.content-none {
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

.content-none {
  align-items: center;
  align-content: center;
  justify-content: center;
}

.direct-date {
  width: 126px;
  display: inline-block;
  vertical-align: top;
  position: absolute;
  left: 0;
}

.top-inner {
  position: absolute;
  left: 126px;
  top: 0;
  right: 0;
  height: 34px;
  overflow: visible;
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: stretch;
  justify-content: space-between;

  & > :nth-child(1) {
    width: 100%;
    max-width: 180px;
    flex: 0 1 100%;
  }

  & > :nth-child(2) {
    width: 100%;
    min-width: 50px;
    flex: 0 1 100%;
  }

  & > :nth-child(3) {
    min-width: 42px;
    max-width: 50px;
    width: 100%;
    flex: 0 0 42px;
  }
}

.content-picker,
.content-none {
  position: absolute;
  top: 34px;
  bottom: 34px;
  left: 0;
  right: 0;
  overflow-y: auto;

  .no_abs & {
    position: static;
  }
}

.bottom-picker {
  bottom: 0;
  display: flex;
  align-items: center;

  .no_abs & {
    position: relative;
  }
}

th {
  text-overflow: ellipsis;
  overflow: hidden;
}

td:not(.nopd):not(.button-td),
th:not(.nopd):not(.button-td) {
  padding: 2px !important;
}

.nopd {
  padding-top: 2px;
  padding-bottom: 2px;
}

.no-first-border-top {
  border-top: none;
  border-bottom: none;

  tr {
    &:first-child {
      border-top: none;

      td {
        border-top: none;
      }
    }

    td:first-child {
      border-left: none;
    }

    td:last-child {
      border-right: none;
    }
  }
}

.status--1 {
  color: #f4d03f;
}

.status-0 {
  color: #cf3a24;
}

.status-1 {
  color: #4b77be;
}

.status-2 {
  color: #049372;
}

.researches {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12px;
}

.button-td {
  padding: 0 !important;
  text-align: right;
  height: 1px;

  .button-td-inner {
    display: flex;
    height: 100%;
    min-height: 24px;
    width: 100%;
    justify-content: flex-end;
    align-items: stretch;

    .btn {
      margin: 0;
      border-radius: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 12px;
      padding: 2px;
      border: none !important;
    }

    &:not(.has_pacs):not(.has_pacs_stationar):not(&-single) {
      .btn {
        flex: 0 0 50%;
      }
    }

    &-single {
      .btn {
        flex: 0 0 100%;
      }
    }

    &.has_pacs_stationar {
      .btn {
        flex: 0 0 32%;
      }

      .btn:nth-child(1) {
        flex: 0 0 20%;
      }

      .btn:nth-child(2) {
        flex: 0 0 16%;
      }
    }

    &.has_pacs {
      .btn {
        flex: 0 0 40%;
      }

      .btn:first-child {
        flex: 0 0 20%;
      }
    }
  }
}

.top-select ::v-deep {
  .btn {
    border-radius: 0;
    border-top: 0;
    height: 34px;
  }
}

.noel {
  text-overflow: clip;
}

.table-one {
  table-layout: fixed;
  margin-bottom: 0;
  position: sticky;
  top: 0;
  background-color: #fff;
  z-index: 1;
}

.table-two {
  table-layout: fixed;
  margin-bottom: 0;
}
</style>
