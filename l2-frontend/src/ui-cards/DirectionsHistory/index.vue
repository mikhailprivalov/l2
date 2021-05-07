<template>
  <div style="height: 100%;width: 100%;position: relative" :class="[!!iss_pk && 'no_abs']">
    <div class="top-picker" v-if="!iss_pk">
      <div class="direct-date" title="Дата направления"
           v-tippy="{ placement : 'right', arrow: true }">
        <date-range small v-model="date_range"/>
      </div>
      <div class="top-inner">
        <div class="top-select">
          <select-picker-m :options="services_options" actions_box multiple
                           noneText="Все услуги" search
                           uid="services_options" v-model="services"/>
        </div>
        <div class="position-relative">
          <button class="btn btn-blue-nb btn-ell dropdown-toggle nbr" data-toggle="dropdown"
                  style="text-align: left!important;width: 100%;"
                  type="button">
            <span class="caret"></span> {{active_type_obj.title}}
          </button>
          <ul class="dropdown-menu">
            <li v-for="row in typesFiltered" :key="row.pk">
              <a :title="row.title"
                 @click.prevent="select_type(row.pk)" href="#">
                {{ row.title }}
              </a>
            </li>
          </ul>
        </div>
        <button class="btn btn-blue-nb btn-ell nbr" title="Обновить" v-tippy @click="load_history_safe">
          <i class="glyphicon glyphicon-refresh"></i>
        </button>
      </div>
    </div>
    <div class="content-picker">
      <table class="table table-responsive table-bordered"
             style="table-layout: fixed;margin-bottom: 0;position:sticky;top:0;background-color: #fff">
        <colgroup>
          <col width="66">
          <col width="70">
          <col>
          <col width="65">
          <col :width="!!iss_pk ? 200 : 150">
          <col width="28">
        </colgroup>
        <thead>
        <tr>
          <th class="text-center">Дата</th>
          <th>№ напр.</th>
          <th>Назначения</th>
          <th class="text-center">Статус</th>
          <th></th>
          <th class="nopd noel"><input type="checkbox" v-model="all_checked"/></th>
        </tr>
        </thead>
      </table>
      <table class="table table-responsive table-bordered no-first-border-top table-hover"
             style="table-layout: fixed;margin-bottom: 0">
        <colgroup>
          <col width="66">
          <col width="70">
          <col>
          <col width="65">
          <col :width="!!iss_pk ? 200 : 150">
          <col width="28">
        </colgroup>
        <tbody>
        <tr v-if="directions.length === 0 && is_created">
          <td class="text-center" :colspan="6">Не найдено</td>
        </tr>
        <tr v-if="directions.length === 0 && !is_created">
          <td class="text-center" :colspan="6">Загрузка...</td>
        </tr>
        <tr v-for="row in directions" :key="row.pk">
          <td class="text-center">{{row.date}}</td>
          <td>
            <span v-if="!!row.has_hosp && role_can_use_stationar">
              <!-- eslint-disable-next-line max-len -->
              <a :href="`/mainmenu/stationar#{%22pk%22:${row.pk},%22opened_list_key%22:null,%22opened_form_pk%22:null,%22every%22:false}`"
                target="_blank" class="a-under">
                {{row.pk}}
              </a>
            </span>
            <span v-else-if="!!row.has_descriptive && role_can_use_descriptive">
              <a
                :href="`/mainmenu/results/paraclinic#{%22pk%22:${row.pk}}`"
                target="_blank" class="a-under">
                {{row.pk}}
              </a>
            </span>
            <span v-else>{{row.pk}}</span>
          </td>
          <td class="researches" :title="row.researches">{{row.researches}}</td>
          <td class="text-center"
              :title="statuses[row.status === 1 && row.has_descriptive ? -2 : row.status] +
                (row.maybe_onco ? '. Онкоподозрение' : '')"
              v-tippy="{ placement : 'bottom', arrow: true }"
              :class="['status-' + row.status]">
            <strong>{{row.status}}<span v-if="row.maybe_onco">*О</span></strong></td>
          <td class="button-td">
            <div class="button-td-inner"
                 :class="[
                   {
                     has_pacs_stationar: !!row.pacs
                     && (!!row.parent.parent_is_hosp || !!row.parent.parent_is_doc_refferal)
                   },
                   {
                     has_pacs: (!!row.pacs && !row.parent.parent_is_hosp)
                      || (!row.pacs && !!row.parent.parent_is_hosp)
                      || (!row.pacs && !!row.parent.parent_is_doc_refferal)
                   }
                 ]">
              <a :href="row.pacs" title="Снимок" v-tippy target="_blank" class="btn btn-blue-nb" v-if="!!row.pacs">
                <i class="fa fa-camera"/>
              </a>
              <a href="#" @click.prevent="role_can_use_stationar ? show_stationar(row.parent.pk) : null"
                 :title="`Принадлежит и/б: ${row.parent.pk}-${row.parent.parent_title}`" v-tippy class="btn btn-blue-nb"
                 v-if="!!row.parent.parent_is_hosp">
                <i class="fa fa-bed"/>
              </a>
              <a href="#" @click.prevent="row.parent.is_confirm ? show_results(row.parent) : null"
                 :title="`Создано в амбулаторном приеме: ${row.parent.pk}-${row.parent.parent_title}`"
                 v-tippy class="btn btn-blue-nb" v-if="!!row.parent.parent_is_doc_refferal"
                 :class="{isDisabled: !row.parent.is_confirm}">
                <i class="fa fa-user-md"/>
              </a>
              <button class="btn btn-blue-nb" title="Штрих-код браслета" v-tippy
                      @click="print_hosp(row.pk)" v-if="row.has_hosp">
                <i class="fa fa-barcode"/> браслета
              </button>
              <button class="btn btn-blue-nb" v-if="row.status <= 1 && !row.has_hosp" @click="cancel_direction(row.pk)">
                Отмена
              </button>
              <button class="btn btn-blue-nb" v-else-if="!row.has_hosp" @click="show_results(row)">Результаты</button>
              <button class="btn btn-blue-nb" @click="print_direction(row.pk)">Направление</button>
            </div>
          </td>
          <td class="nopd"><input v-model="row.checked" type="checkbox"/></td>
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

<script>
import moment from 'moment';
import { mapGetters } from 'vuex';
import SelectPickerM from '../../fields/SelectPickerM.vue';
import DateRange from '../DateRange.vue';
import directionsPoint from '../../api/directions-point';
import * as actions from '../../store/action-types';
import Bottom from './Bottom/index.vue';

function truncate(s, n, useWordBoundary) {
  if (!s) {
    return '';
  }
  if (s.length <= n) {
    return s;
  }
  const subString = s.substr(0, n - 1);
  return `${useWordBoundary
    ? subString.substr(0, subString.lastIndexOf(' '))
    : subString}...`;
}

export default {
  components: { SelectPickerM, DateRange, Bottom },
  name: 'directions-history',
  props: {
    patient_pk: {
      type: Number,
      default: -1,
      required: false,
    },
    iss_pk: {
      type: Number,
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
  },
  data() {
    return {
      date_range: [moment().subtract(6, 'month').format('DD.MM.YY'), moment().format('DD.MM.YY')],
      types: [
        { pk: 3, title: 'Направления пациента' },
        { pk: 0, title: 'Только выписанные' },
        { pk: 1, title: 'Материал в лаборатории' },
        { pk: 2, title: 'Результаты подтверждены' },
        { pk: 4, title: 'Созданы пользователем' },
      ],
      active_type: 3,
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
      return this.types.filter(t => t.pk !== this.active_type);
    },
    role_can_use_stationar() {
      for (const g of (this.$store.getters.user_data.groups || [])) {
        if (g === 'Врач стационара') {
          return true;
        }
      }
      return false;
    },
    role_can_use_descriptive() {
      for (const g of (this.$store.getters.user_data.groups || [])) {
        if (['Врач консультаций', 'Врач параклиники'].includes(g)) {
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
      researches_obj: 'researches',
    }),
  },
  mounted() {
    this.is_created = true;
    this.load_history();
    this.$root.$on(`researches-picker:directions_created${this.kk}`, this.load_history);
    this.$root.$on(`researches-picker:refresh${this.kk}`, this.load_history_safe);
  },
  methods: {
    async load_history_safe() {
      await this.load_history(true);
    },
    update_so(researches) {
      const s = Object.values(researches || {}).map((r) => ({
        value: String(r.pk),
        label: truncate(r.full_title || r.title, 70, true),
      }));
      if (s.length === 0) {
        return;
      }
      s.sort((a, b) => ((a.label.toUpperCase() > b.label.toUpperCase()) ? 1 : -1));
      this.services_options = s;
      setTimeout(() => {
        this.$root.$emit('update-sp-m-services_options');
      }, 0);
    },
    show_stationar(dir) {
      const path = `/mainmenu/stationar#{%22pk%22:${dir},%22opened_list_key%22:null,%22opened_form_pk%22:null,%22every%22:false}`;
      window.open(path, '_blank');
    },
    show_results(row) {
      if (row.has_descriptive) {
        this.$root.$emit('print:results', [row.pk]);
      } else {
        this.$root.$emit('show_results', row.pk);
      }
    },
    print_direction(pk) {
      this.$root.$emit('print:directions', [pk]);
    },
    print_hosp(pk) {
      this.$root.$emit('print:hosp', [pk]);
    },
    async cancel_direction(pk) {
      await this.$store.dispatch(actions.INC_LOADING);

      const data = await directionsPoint.cancelDirection({ pk });

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
    async load_history(safe) {
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

      await directionsPoint.getHistory(this, ['iss_pk', 'services', 'forHospSlave'], {
        type: this.active_type,
        patient: this.patient_pk,
        date_from: moment(this.date_range[0], 'DD.MM.YY').format('DD.MM.YYYY'),
        date_to: moment(this.date_range[1], 'DD.MM.YY').format('DD.MM.YYYY'),
      }).then((data) => {
        this.directions = data.directions;
        for (const d of this.directions) {
          if (checked.includes(d.pk)) {
            d.checked = true;
          }
        }
      }).finally(() => {
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
        this.checked = this.checked.filter((e) => e !== pk);
      } else if (!this.in_checked(pk)) {
        this.checked.push(pk);
      }
    },
  },
  watch: {
    active_type() {
      this.load_history();
    },
    patient_pk() {
      this.load_history();
    },
    date_range() {
      this.load_history();
    },
    services() {
      this.load_history();
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
};
</script>

<style scoped lang="scss">
  .isDisabled {
    cursor: not-allowed;
    opacity: 0.7;
  }

  .top-picker, .bottom-picker {
    height: 34px;
    background-color: #AAB2BD;
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
        border-bottom: 1px solid #AAB2BD;
        background: #fff;
      }

      .input-group-addon {
        border: 1px solid #AAB2BD;
        border-top: none;
      }
    }
  }

  .content-picker, .content-none {
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

  .content-picker, .content-none {
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

  td:not(.nopd):not(.button-td), th:not(.nopd):not(.button-td) {
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
    color: #F4D03F
  }

  .status-0 {
    color: #CF3A24
  }

  .status-1 {
    color: #4B77BE
  }

  .status-2 {
    color: #049372
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

      &:not(.has_pacs) {
        .btn {
          flex: 0 0 50%;
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
</style>
