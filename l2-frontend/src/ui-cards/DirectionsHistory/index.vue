<template>
  <div style="height: 100%;width: 100%;position: relative" :class="[!!iss_pk && 'no_abs']">
    <div class="top-picker" v-if="!iss_pk">
      <div style="width: 126px;display: inline-block;vertical-align: top" title="Дата направления"
           v-tippy="{ placement : 'right', arrow: true }">
        <date-range small v-model="date_range"/>
      </div>
      <div class="top-inner">
        <div class="top-select" style="width: 180px">
          <select-picker-m :options="services_options" actions_box multiple
                           noneText="Все услуги" search
                           uid="services_options" v-model="services"/>
        </div>
        <div style="flex: 0 calc(100% - 230px);position: relative;">
          <button class="btn btn-blue-nb btn-ell dropdown-toggle" data-toggle="dropdown"
                  style="text-align: left!important;border-radius: 0;width: 100%;"
                  type="button">
            <span class="caret"></span> {{active_type_obj.title}}
          </button>
          <ul class="dropdown-menu">
            <li><a :title="row.title" @click.prevent="select_type(row.pk)" href="#" v-for="row in types"
                   v-if="row.pk !== active_type">{{ row.title }}</a></li>
          </ul>
        </div>
        <button class="btn btn-blue-nb btn-ell" style="border-radius: 0;width: 50px;flex: 1 50px;" title="Обновить"
                @click="load_history">
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
          <td class="text-center" :colspan="!iss_pk ? 6 : 5">Не найдено</td>
        </tr>
        <tr v-if="directions.length === 0 && !is_created">
          <td class="text-center" :colspan="!iss_pk ? 6 : 5">Загрузка...</td>
        </tr>
        <tr v-for="row in directions">
          <td class="text-center">{{row.date}}</td>
          <td>{{row.pk}}</td>
          <td class="researches" :title="row.researches">{{row.researches}}</td>
          <td class="text-center"
              :title="statuses[row.status === 1 && row.has_descriptive ? -2 : row.status] +
                (row.maybe_onco ? '. Онкоподозрение' : '')"
              v-tippy="{ placement : 'bottom', arrow: true }"
              :class="['status-' + row.status]">
            <strong>{{row.status}}<span v-if="row.maybe_onco">*О</span></strong></td>
          <td class="button-td">
            <div class="button-td-inner" :class="[{has_pacs_stationar: !!row.pacs && !!row.parent.parent_is_hosp || !!row.pacs && !!row.parent.parent_is_doc_refferal},
                 {has_pacs: (!!row.pacs && !row.parent.parent_is_hosp) || (!row.pacs && !!row.parent.parent_is_hosp) || !row.pacs && !!row.parent.parent_is_doc_refferal}]">
              <a :href="row.pacs" title="Снимок" v-tippy target="_blank" class="btn btn-blue-nb" v-if="!!row.pacs">
                <i class="fa fa-camera"/>
              </a>
              <a :href="`/mainmenu/stationar#{%22pk%22:${row.parent.pk},%22opened_list_key%22:null,%22opened_form_pk%22:null,%22every%22:false}`"
                 :title="'Принадлежит и/б: ' + [[row.parent.pk]] + '-' + [[row.parent.parent_title]]" v-tippy target="_blank" class="btn btn-blue-nb" v-if="!!row.parent.parent_is_hosp">
                <i class="fa fa-bed"/>
              </a>
              <a @click="row.parent.is_confirm ? show_results(row.parent) : null" :title="'Создано в амбулаторном приеме: ' + [[row.parent.pk]] + '-' + [[row.parent.parent_title]]"
                 v-tippy target="_blank" class="btn btn-blue-nb" v-if="!!row.parent.parent_is_doc_refferal" :class="{isDisabled: !row.parent.is_confirm}">
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
    <div class="bottom-picker" v-if="checked.length > 0 || !iss_pk">
      <div style="padding-left: 5px;color: #fff"><span v-if="checked.length > 0">Отмечено: {{checked.length}}</span>
      </div>
      <div class="bottom-inner">
        <div class="dropup" style="display: inline-block;max-width: 350px;width: 100%">
          <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                  style="text-align: right!important;border-radius: 0;width: 100%">
            Действие с отмеченными <span class="caret"></span>
          </button>
          <ul class="dropdown-menu">
            <li v-for="f in forms" v-if="patient_pk !== -1 && (!f.need_dirs || checked.length > 0)">
              <a :href="f.url" target="_blank">{{f.title}}</a>
            </li>
            <li v-for="(value, k) in menuItems">
              <a href="#"
                 v-if="(!value.onlyNotForIssledovaniye || !iss_pk)
                  && (!value.onlyForTypes || value.onlyForTypes.includes(active_type))"
                 @click.prevent="value.handler.bind(this)">
                {{value.title}}
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
    <directions-change-parent
      v-if="change_parent_open"
      :card_pk="patient_pk"
      :direction_checked="checked"
    />
  </div>
</template>

<script>
  import SelectPickerM from '../../fields/SelectPickerM'
  import DateRange from '../DateRange'
  import directions_point from '../../api/directions-point'
  import * as action_types from '../../store/action-types'
  import moment from 'moment'
  import {forDirs} from '../../forms';
  import {mapGetters} from 'vuex'
  import DirectionsChangeParent from '../../modals/DirectionsChangeParent'
  import menuMixin from './mixins/menu'

  function truncate(s, n, useWordBoundary) {
    if (s.length <= n) {
      return s
    }
    const subString = s.substr(0, n - 1)
    return (useWordBoundary
      ? subString.substr(0, subString.lastIndexOf(' '))
      : subString) + '...'
  }

  export default {
    mixins: [menuMixin],
    components: {DirectionsChangeParent, SelectPickerM, DateRange},
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
        date_range: [moment().subtract(3, 'month').format('DD.MM.YY'), moment().format('DD.MM.YY')],
        types: [
          {pk: 3, title: 'Направления пациента'},
          {pk: 0, title: 'Только выписанные'},
          {pk: 1, title: 'Материал в лаборатории'},
          {pk: 2, title: 'Результаты подтверждены'},
          {pk: 4, title: 'Созданы пользователем'}
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
          '0': 'Направление только выписано',
          '1': 'Материал в лаборатории',
          '2': 'Результаты подтверждены',
        },
        change_parent_open: false,
      }
    },
    computed: {
      forms() {
        return forDirs.map(f => {
          return {
            ...f, url: f.url.kwf({
              card: this.patient_pk,
              dir: JSON.stringify(this.checked),
            })
          }
        });
      },
      active_type_obj() {
        for (let row of this.types) {
          if (row.pk === this.active_type) {
            return row
          }
        }
        return {}
      },
      ...mapGetters({
        researches: 'researches',
      }),
    },
    mounted() {
      this.is_created = true
      this.load_history()
      this.$root.$on('researches-picker:directions_created' + this.kk, this.load_history)
      this.$root.$on('hide_pe', () => this.change_parent_hide());
    },
    methods: {
      update_so(researches) {
        const s = [].concat.apply([], Object.values(researches)).map(r => ({
          value: String(r.pk),
          label: truncate(r.full_title, 60, true),
        }))
        if (s.length === 0) {
          return
        }
        s.sort((a, b) => (a.label.toUpperCase() > b.label.toUpperCase()) ? 1 : -1)
        this.services_options = s
        setTimeout(() => {
          this.$root.$emit(`update-sp-m-services_options`)
        }, 0)
      },
      show_results(row) {
        if (row.has_descriptive) {
          this.$root.$emit('print:results', [row.pk])
        } else {
          this.$root.$emit('show_results', row.pk)
        }
      },
      print_direction(pk) {
        this.$root.$emit('print:directions', [pk])
      },
      print_hosp(pk) {
        this.$root.$emit('print:hosp', [pk])
      },
      async cancel_direction(pk) {
        await this.$store.dispatch(action_types.INC_LOADING)

        const data = await directions_point.cancelDirection({pk});

        for (let dir of this.directions) {
          if (dir.pk === pk) {
            dir.cancel = data.cancel
            if (dir.status === -1 && !dir.cancel) {
              dir.status = 0
            } else if (dir.status === 0 && dir.cancel) {
              dir.status = -1
            }
            break
          }
        }

        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      select_type(pk) {
        this.active_type = pk
      },
      load_history() {
        if (!this.is_created)
          return
        this.$root.$emit('validate-datepickers')
        this.is_created = false
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        vm.directions = []
        vm.all_checked = false

        directions_point.getHistory(this, ['iss_pk', 'services', 'forHospSlave'], {
          type: this.active_type,
          patient: this.patient_pk,
          date_from: moment(this.date_range[0], 'DD.MM.YY').format('DD.MM.YYYY'),
          date_to: moment(this.date_range[1], 'DD.MM.YY').format('DD.MM.YYYY'),
        }).then((data) => {
          vm.directions = data.directions
        }).finally(() => {
          vm.is_created = true
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      in_checked(pk) {
        return this.checked.indexOf(pk) !== -1
      },
      sync_check(pk, e) {
        let v = e.target.checked
        if (!v) {
          this.checked = this.checked.filter(e => e !== pk)
        } else if (!this.in_checked(pk)) {
          this.checked.push(pk)
        }
      },
      change_parent_hide() {
        this.change_parent_open = false
      },

    },
    watch: {
      active_type() {
        this.load_history()
      },
      patient_pk() {
        this.load_history()
      },
      date_range() {
        this.load_history()
      },
      services() {
        this.load_history()
      },
      all_checked() {
        for (let row of this.directions) {
          row.checked = this.all_checked
        }
      },
      directions: {
        handler() {
          this.checked = []
          for (let row of this.directions) {
            if (row.checked) {
              this.checked.push(row.pk)
            }
          }
        },
        deep: true
      },
      researches: {
        handler() {
          this.update_so(this.researches)
        },
        immediate: true,
      },
    }
  }
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

    /deep/ {
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

  .content-picker, .content-none, .bottom-inner {
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

  .bottom-inner {
    position: absolute;
    color: #fff;
    height: 34px;
    right: 0;
    left: 155px;
    top: 0;
    justify-content: flex-end;
    align-content: center;
    align-items: center;
    overflow: visible;
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

  .top-select /deep/ {
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
