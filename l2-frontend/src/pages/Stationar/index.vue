<template>
  <div ref="root" class="root">
    <div class="sidebar">
      <div class="sidebar-top">
        <input type="text" class="form-control" v-model="pk" @keyup.enter="load" autofocus
               placeholder="Номер истории"/>
        <button class="btn btn-blue-nb" @click="load" :disabled="pk === ''">Загрузить</button>
      </div>
      <div class="sidebar-content">
        <div class="inner" v-if="direction !== null && patient !== null">
          <div class="inner-card">
            История болезни №{{direction}}
          </div>
          <div class="inner-card">
            {{issTitle}}
          </div>
          <patient-card :patient="patient" class="inner-card"/>
          <div class="sidebar-btn-wrapper"
               v-for="(title, key) in menuItems"
               :key="key">
            <button class="btn btn-blue-nb sidebar-btn"
                    @click="load_directions(key)"
            >
              <span v-if="Boolean(counts[key])" class="counts">{{counts[key]}} шт.</span> {{title}}
            </button>
            <button class="btn btn-blue-nb sidebar-btn"
                    v-if="menuNeedPlus[key]"
                    @click="plus(key)"
            >
              <i class="fa fa-plus"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="content">
      <div class="top">
        <div class="top-block title-block" v-if="opened_list_key">
          <span>{{menuItems[opened_list_key]}}</span>
          <i class="fa fa-times" @click="close_list_directions"/>
        </div>
        <div class="top-block direction-block" :key="d.pk" v-for="d in list_directions">
          {{d.pk}}
        </div>
      </div>
      <div class="inner">

      </div>
    </div>
    <modal @close="closePlus" marginLeftRight="auto"
           margin-top="60px"
           max-width="1400px" ref="modalStationar" show-footer="true"
           v-if="openPlusMode === 'directions'"
           white-bg="true" width="100%">
      <span slot="header">Создание направлений – история {{direction}} {{issTitle}}, {{patient.fio_age}}</span>
      <div class="registry-body" slot="body" style="min-height: 140px">
        <div class="row">
          <div class="col-xs-6"
               style="height: 450px;border-right: 1px solid #eaeaea;padding-right: 0;">
            <researches-picker v-model="create_directions_data"
                               :types-only="pickerTypesOnly"
                               kk="stationar"
                               style="border-top: 1px solid #eaeaea;border-bottom: 1px solid #eaeaea;"/>
          </div>
          <div class="col-xs-6" style="height: 450px;padding-left: 0;">
            <selected-researches
              kk="stationar"
              :base="bases_obj[patient.base]"
              :researches="create_directions_data"
              :main_diagnosis="'-'"
              :valid="true"
              :card_pk="patient.cardId"
              :initial_fin="finId"
              :parent_iss="iss"
              :clear_after_gen="true"
              style="border-top: 1px solid #eaeaea;border-bottom: 1px solid #eaeaea;"
            />
          </div>
        </div>
        <div v-if="create_directions_data.length > 0"
             style="margin-top: 5px;text-align: left">
          <table class="table table-bordered lastresults">
            <colgroup>
              <col width="180">
              <col>
              <col width="110">
              <col width="110">
            </colgroup>
            <tbody>
            <last-result :individual="patient.individualId" :key="p" v-for="p in create_directions_data"
                         :parent-iss="iss"
                         :noScroll="true"
                         :research="p"/>
            </tbody>
          </table>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="closePlus" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </modal>
    <modal v-if="openPlusMode === 'stationar'" ref="modalStationar2" @close="closePlus"
           margin-top="50px"
           show-footer="true" white-bg="true" max-width="710px" width="100%" marginLeftRight="auto">
      <span slot="header">{{menuItems[openPlusId]}} – история {{direction}} {{issTitle}}, {{patient.fio_age}}</span>
      <div slot="body" style="min-height: 200px;background-color: #fff" class="registry-body">
        <div class="text-left">
          <div class="content-picker">
            <research-pick :class="{ active: row.pk === direction_service }" :research="row"
                           @click.native="select_research(row.pk)"
                           class="research-select"
                           v-for="row in hosp_services"
                           :key="row.pk"/>
            <div v-if="hosp_services.length === 0">не настроено</div>
          </div>
          <div class="text-center" style="margin-top: 10px;">
            <button @click="confirm_service"
                    :disabled="direction_service === -1"
                    class="btn btn-primary-nb btn-blue-nb" type="button">
              Сохранить назначение и заполнить протокол
            </button>
          </div>
        </div>
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button @click="closePlus" class="btn btn-primary-nb btn-blue-nb" type="button">
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </modal>
  </div>
</template>

<script>
  import {mapGetters} from 'vuex'
  import menuMixin from './mixins/menu'
  import * as action_types from '../../store/action-types'
  import stationar_point from '../../api/stationar-point'
  import PatientCard from './PatientCard'
  import Patient from '../../types/patient'
  import Modal from '../../ui-cards/Modal'
  import ResearchesPicker from '../../ui-cards/ResearchesPicker'
  import LastResult from '../../ui-cards/LastResult'
  import SelectedResearches from '../../ui-cards/SelectedResearches'
  import ResearchPick from '../../ui-cards/ResearchPick'

  export default {
    mixins: [menuMixin],
    components: {ResearchPick, SelectedResearches, LastResult, ResearchesPicker, Modal, PatientCard},
    data() {
      return {
        pk: '',
        direction: null,
        iss: null,
        issTitle: null,
        finId: null,
        counts: {},
        patient: new Patient({}),
        openPlusMode: null,
        openPlusId: null,
        create_directions_data: [],
        hosp_services: [],
        direction_service: -1,
        list_directions: [],
        opened_list_key: null,
      }
    },
    watch: {
      pk() {
        this.pk = this.pk.replace(/\D/g, '')
      }
    },
    methods: {
      async confirm_service() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const {pk} = await stationar_point.makeService({
          service: this.direction_service,
          main_direction: this.direction,
        })
        console.log({pk})
        this.counts = await stationar_point.counts(this, ['direction'])
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      select_research(pk) {
        this.direction_service = pk
      },
      async load() {
        this.direction = null
        this.iss = null
        this.issTitle = null
        this.finId = null
        this.counts = {}
        this.patient = new Patient({})
        this.openPlusId = null
        this.openPlusMode = null
        this.create_directions_data = []
        await this.$store.dispatch(action_types.INC_LOADING)
        const {ok, data, message} = await stationar_point.load(this, ['pk'])
        if (ok) {
          this.pk = ''
          this.direction = data.direction
          this.iss = data.iss
          this.issTitle = data.iss_title
          this.finId = data.fin_pk
          this.patient = new Patient(data.patient)
          this.counts = await stationar_point.counts(this, ['direction'])
        } else {
          errmessage(message)
        }
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      close_list_directions() {
        this.list_directions = []
        this.opened_list_key = null
      },
      async load_directions(key) {
        await this.$store.dispatch(action_types.INC_LOADING)
        const {data} = await stationar_point.directionsByKey({
          direction: this.direction,
          r_type: key,
        })
        this.list_directions = data
        this.opened_list_key = key
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
      async plus(key) {
        const mode = this.plusDirectionsMode[key] ? 'directions' : 'stationar'
        if (mode === 'stationar') {
          await this.$store.dispatch(action_types.INC_LOADING)
          const {data} = await stationar_point.hospServicesByType({
            direction: this.direction,
            r_type: key,
          })
          this.hosp_services = data
          if (data.length === 1) {
            this.direction_service = data[0].pk
          }
          await this.$store.dispatch(action_types.DEC_LOADING)
        }
        this.openPlusMode = mode
        this.openPlusId = key
      },
      async closePlus() {
        this.openPlusMode = null
        this.openPlusId = null
        this.create_directions_data = []
        this.hosp_services = []
        this.direction_service = -1

        if (this.$refs.modalStationar && this.$refs.modalStationar.$el) {
          this.$refs.modalStationar.$el.style.display = 'none'
        }

        if (this.$refs.modalStationar2 && this.$refs.modalStationar2.$el) {
          this.$refs.modalStationar2.$el.style.display = 'none'
        }

        this.$store.dispatch(action_types.INC_LOADING).then()
        this.counts = await stationar_point.counts(this, ['direction'])
        this.$store.dispatch(action_types.DEC_LOADING).then()
      }
    },
    computed: {
      ...mapGetters({
        user_data: 'user_data',
        researches: 'researches',
        bases: 'bases',
      }),
      bases_obj() {
        return this.bases.reduce((a, b) => ({
          ...a,
          [b.pk]: b,
        }), {})
      },
      pickerTypesOnly() {
        if (this.openPlusId === 'laboratory') {
          return [2]
        }
        if (this.openPlusId === 'paraclinical') {
          return [3]
        }
        if (this.openPlusId === 'consultation') {
          return [4]
        }
        return []
      },
    }
  }
</script>

<style scoped lang="scss">
  .root {
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;

    & > div {
      align-self: stretch;
    }
  }

  .sidebar {
    width: 260px;
    border-right: 1px solid #b1b1b1;
    display: flex;
    flex-direction: column;
  }

  .content {
    display: flex;
    flex-direction: column;
    width: calc(100% - 260px);
    border: none;

    .top {
      border-bottom: 1px solid #b1b1b1;
      height: 63px;
      padding: 5px;
      overflow-x: auto;
      overflow-y: visible;
      white-space: nowrap;

      .top-block {
        display: inline-flex;
        vertical-align: top;
        height: 100%;
        white-space: normal;
        width: 130px;
        padding: 3px;
        margin-right: 3px;
        border-radius: 3px;
        border: 1px solid rgba(0, 0, 0, 0.14);
        background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
      }

      .title-block {
        position: relative;
        align-items: center;
        justify-content: center;
        margin-right: 0;

        span {
          align-self: center;
        }

        i {
          position: absolute;
          top: 0;
          right: 0;
          padding: 3px;
          color: lightgray;
          cursor: pointer;

          &:hover {
            color: #000;
          }
        }
      }
    }

    .inner {
      height: calc(100% - 63px);
      overflow-y: auto;
      overflow-x: hidden;
    }
  }

  .sidebar-top {
    flex: 0 0 34px;
    display: flex;
    flex-direction: row;
    align-items: stretch;
    flex-wrap: nowrap;
    justify-content: stretch;

    input, button {
      align-self: stretch;
      border: none;
      border-radius: 0;
    }

    input {
      border-bottom: 1px solid #b1b1b1;
      width: 166px !important;
      flex: 2 166px;
    }

    button {
      flex: 3 94px;
      width: 94px
    }
  }

  .sidebar-content {
    position: relative;
    height: calc(100% - 34px);

    .inner {
      height: 100%;
      overflow-y: auto;
      overflow-x: hidden;

      &-card {
        width: 100%;
        background: #fff;
        border-bottom: 1px solid #b1b1b1 !important;
        padding: 4px 12px;
      }
    }
  }

  .sidebar-btn {
    border-radius: 0;
    text-align: left;
    border-top: none !important;
    border-right: none !important;
    border-left: none !important;
    padding: 0 12px;
    height: 24px;

    &:not(:hover) {
      background-color: rgba(#000, .02) !important;
      color: #000;
      border-bottom: 1px solid #b1b1b1 !important;
    }
  }

  .sidebar-btn-wrapper {
    display: flex;
    flex-direction: row;

    .sidebar-btn:first-child {
      flex: 1 1 auto;
    }
  }

  .lastresults {
    table-layout: fixed;
    padding: 0;
    margin: 0;
    color: #000;
    background-color: #ffdb4d;
    border-color: #000;

    /deep/ th, /deep/ td {
      border-color: #000;
    }

    /deep/ a {
      color: #000;
      text-decoration: dotted underline;
    }

    /deep/ a:hover {
      text-decoration: none;
    }
  }

  .counts {
    float: right;
  }

  .content-picker {
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    align-items: stretch;
    align-content: flex-start;
  }

  .research-select {
    align-self: stretch;
    display: flex;
    align-items: center;
    padding: 1px 2px 1px;
    color: #000;
    background-color: #fff;
    text-decoration: none;
    transition: .15s linear all;
    margin: 0;
    font-size: 12px;
    min-width: 0;
    flex: 0 1 auto;
    width: 25%;
    height: 34px;
    border: 1px solid #6C7A89 !important;
    cursor: pointer;
    text-align: left;
    outline: transparent;

    &.active {
      background: #049372 !important;
      color: #fff;
    }

    &:hover {
      box-shadow: inset 0 0 8px rgba(0, 0, 0, .8) !important;
    }
  }
</style>
