<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <div style="align-self: stretch;display: inline-flex;align-items: center;padding: 1px 0 1px 5px;
      flex: 1;margin: 0;font-size: 12px;width: 87px;color:#fff">
        <span
          style="display: block;max-height: 2.2em;line-height: 1.1em;vertical-align: top">Дата<br/>направления:</span>
      </div>
      <div style="width: 186px;display: inline-block;vertical-align: top">
        <date-range v-model="date_range"/>
      </div>
      <div class="top-inner">
        <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                style="text-align: left!important;border-radius: 0;width: 100%">
          <span class="caret"></span> {{active_type_obj.title}}
        </button>
        <ul class="dropdown-menu">
          <li><a v-if="row.pk !== active_type" href="#" @click.prevent="select_type(row.pk)" v-for="row in types"
                 :title="row.title">{{ row.title }}</a></li>
        </ul>
        <button class="btn btn-blue-nb btn-ell" style="border-radius: 0;width: 50px;" title="Обновить"
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
          <col width="150">
          <col width="28">
        </colgroup>
        <thead>
        <tr>
          <th class="text-center">Дата</th>
          <th>№ напр.</th>
          <th>Назначения</th>
          <th class="text-center">Статус</th>
          <th></th>
          <th class="nopd"><input type="checkbox" v-model="all_checked"/></th>
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
          <col width="150">
          <col width="28">
        </colgroup>
        <tbody>
        <tr v-if="directions.length === 0 && is_created">
          <td class="text-center" colspan="6">Не найдено</td>
        </tr>
        <tr v-if="directions.length === 0 && !is_created">
          <td class="text-center" colspan="6">Загрузка...</td>
        </tr>
        <tr v-for="row in directions">
          <td class="text-center">{{row.date}}</td>
          <td>{{row.pk}}</td>
          <td class="researches" :title="row.researches">{{row.researches}}</td>
          <td class="text-center" :title="statuses[row.status === 1 && row.has_descriptive ? -2 : row.status]"
              v-tippy="{ placement : 'bottom', arrow: true }"
              :class="['status-' + row.status]">
            <strong>{{row.status}}</strong></td>
          <td class="button-td">
            <div class="button-td-inner">
              <button class="btn btn-blue-nb" v-if="row.status <= 1" @click="cancel_direction(row.pk)">Отмена</button>
              <button class="btn btn-blue-nb" v-else @click="show_results(row)">Результаты</button>
              <button class="btn btn-blue-nb" @click="print_direction(row.pk)">Направление</button>
            </div>
          </td>
          <td class="nopd"><input v-model="row.checked" type="checkbox"/></td>
        </tr>
        </tbody>
      </table>
    </div>
    <div class="bottom-picker">
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
            <li><a href="#" @click.prevent="selected_do('directions_list')">Создать список назначений</a></li>
            <li><a href="#" @click.prevent="selected_do('copy_researches')">Скопировать исследования для назначения</a></li>
            <li><a href="#" @click.prevent="selected_do('print_results')">Печать результатов</a></li>
            <li><a href="#" @click.prevent="selected_do('print_barcodes')">Печать штрих-кодов</a></li>
            <li><a href="#" @click.prevent="selected_do('print_directions')">Печать направлений</a></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import DateRange from './ui-cards/DateRange'
  import directions_point from './api/directions-point'
  import * as action_types from './store/action-types'
  import moment from 'moment'
  import {forDirs} from './forms';

  export default {
    components: {DateRange},
    name: 'directions-history',
    props: {
      patient_pk: {
        type: Number,
        default: -1
      }
    },
    data() {
      return {
        date_range: [moment().subtract(3, 'month').format('DD.MM.YYYY'), moment().format('DD.MM.YYYY')],
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
        all_checked: false,
        statuses: {
          '-2': 'Посещение зарегистрировано',
          '-1': 'Направление отменено',
          '0': 'Направление только выписано',
          '1': 'Материал в лаборатории',
          '2': 'Результаты подтверждены',
        }
      }
    },
    computed: {
      forms() {
        return forDirs.map(f => {
          return {...f, url: f.url.kwf({
              card: this.patient_pk,
              dir: JSON.stringify(this.checked),
            })}
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
    },
    mounted() {
      this.is_created = true
      this.load_history()
    },
    created() {
      this.$root.$on('researches-picker:directions_created', this.load_history)
    },
    methods: {
      show_results(row) {
        if (row.has_descriptive) {
          this.$root.$emit('print:results', [row.pk])
        }
        else {
          this.$root.$emit('show_results', row.pk)
        }
      },
      print_direction(pk) {
        this.$root.$emit('print:directions', [pk])
      },
      cancel_direction(pk) {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        directions_point.cancelDirection(pk).then((data) => {
          for (let dir of vm.directions) {
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
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })

      },
      selected_do(type) {
        switch (type) {
          case 'resend_results_rmis':
            break
          case 'resend_directions_rmis':
            break
          case 'copy_researches':
            for (let dir of this.directions) {
              if (this.in_checked(dir.pk)) {
                for (let pk of dir.researches_pks) {
                  this.$root.$emit('researches-picker:add_research', pk)
                }
              }
            }
            break
          case 'print_results':
            this.$root.$emit('print:results', this.checked)
            break
          case 'print_barcodes':
            this.$root.$emit('print:barcodes', this.checked)
            break
          case 'directions_list':
            this.$root.$emit('print:directions_list', this.checked)
            break
          default:
            this.$root.$emit('print:directions', this.checked)
            break
        }
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
        directions_point.getHistory(this.active_type, this.patient_pk, this.date_range[0], this.date_range[1]).then((data) => {
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
        }
        else if (!this.in_checked(pk)) {
          this.checked.push(pk)
        }
      }
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
      }
    }
  }
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
    left: 278px;
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
  }

  .bottom-picker {
    bottom: 0;
    display: flex;
    align-items: center;
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
    }

    .btn {
      margin: 0;
      border-radius: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 12px;
      padding: 2px;
      border: none !important;
      flex: 0 0 50%;
    }
  }
</style>
