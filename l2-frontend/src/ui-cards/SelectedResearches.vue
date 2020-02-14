<template>
  <div style="height: 100%;width: 100%;position: relative" :class="[pay_source && 'pay_source']">
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
        <a href="#" @click.prevent="select_fin(row.pk)" class="top-inner-select" :class="{ active: row.pk === fin}"
           v-for="row in base.fin_sources"><span>{{ row.title }}</span></a>
      </div>
    </div>
    <div :class="['content-picker', simple ? 'simple': '']" style="margin: 5px">
      <table class="table table-bordered table-condensed" style="table-layout: fixed; margin-bottom: 10px;">
        <colgroup>
          <col width="130">
          <col>
          <col width="38" v-if="!readonly">
        </colgroup>
        <tbody>
        <tr v-for="(row, key) in researches_departments">
          <td>{{row.title}}</td>
          <td class="pb0">
            <research-display v-for="(res, idx) in row.researches" :simple="simple"
                              :key="res.pk"
                              :title="res.title" :pk="res.pk" :n="idx"
                              :kk="kk"
                              :comment="(localizations[res.pk] || {}).label || comments[res.pk]"
                              :count="counts[res.pk]"
                              :service_location="(service_locations[res.pk] || {}).label"
                              :nof="row.researches.length"/>
          </td>
          <td v-if="!readonly" class="cl-td">
            <button class="btn last btn-blue-nb nbr" type="button"
                    v-tippy="{ placement : 'bottom', arrow: true }"
                    :title="`Очистить категорию ${row.title}`" @click.prevent="clear_department(parseInt(key))">
              <i class="fa fa-times"></i>
            </button>
          </td>
        </tr>
        <tr v-if="Object.keys(researches_departments).length > 1 && !readonly">
          <td colspan="2"></td>
          <td class="cl-td">
            <button class="btn last btn-blue-nb nbr" type="button"
                    v-tippy="{ placement : 'bottom', arrow: true }"
                    title="Очистить всё" @click.prevent="clear_all">
              <i class="fa fa-times-circle"></i>
            </button>
          </td>
        </tr>
        </tbody>
      </table>
      <table class="table table-bordered table-condensed" style="table-layout: fixed" v-if="show_additions">
        <colgroup>
          <col width="160">
          <col>
        </colgroup>
        <tbody>
          <tr v-if="direction_purpose_enabled">
            <th>Цель направления:</th>
            <td class="cl-td">
              <SelectFieldTitled v-model="direction_purpose" :variants="purposes" />
            </td>
          </tr>
          <tr>
            <th>Количество:</th>
            <td class="cl-td">
              <input v-model="directions_count" min="1" max="10"
                     style="max-width: 160px" class="form-control" type="number" step="1"/>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="bottom-picker-inputs" v-if="pay_source">
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
      <div class="top-inner-select" :class="{ disabled: !can_save }" @click="generate('direction')"
           title="Сохранить и распечатать направления"><span>Сохранить и распечатать направления</span></div>
      <div class="top-inner-select" :class="{ disabled: !can_save }" @click="generate('barcode')"
           title="Сохранить и распечатать штрих-коды"><span>Сохранить и распечатать штрих-коды</span></div>
      <div class="top-inner-select" :class="{ disabled: !can_save }" @click="generate('just-save')"
           title="Сохранить без печати"><span>Сохранить без печати</span></div>
    </div>

    <modal ref="modal" @close="cancel_update" show-footer="true"
           overflow-unset="true"
           v-show="need_update_comment.length > 0 && !hide_window_update && !simple">
      <span slot="header">Настройка назначений</span>
      <div slot="body" class="overflow-unset">
        <table class="table table-bordered table-responsive"
               style="table-layout: fixed;background-color: #fff;margin: 0 auto;">
          <colgroup>
            <col width="260">
            <col width="300">
            <col width="300">
            <col width="80">
          </colgroup>
          <thead>
          <tr>
            <th>Назначение</th>
            <th>Комментарий</th>
            <th>Место оказания</th>
            <th>Количество</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="row in need_update_object">
            <td>
              <div style="width:100%; overflow: hidden;text-overflow: ellipsis;" :title="row.title">{{row.title}}</div>
            </td>
            <td>
              <v-select :clearable="false" :options="row.localizations"
                        :searchable="false" v-if="row.localizations && row.localizations.length > 0"
                        v-model="localizations[row.pk]"/>
              <v-select :options="row.options" taggable v-else v-model="comments[row.pk]">
                <div slot="no-options">Нет вариантов по умолчанию</div>
              </v-select>
            </td>
            <td>
              <v-select :clearable="false" :options="row.service_locations"
                        :searchable="false" v-if="row.service_locations && row.service_locations.length > 0"
                        v-model="service_locations[row.pk]"/>
              <div style="text-align: center;padding: 3px;color: lightslategray;font-size: 90%" v-else>
                нет доступных вариантов
              </div>
            </td>
            <td>
              <input class="form-control" type="number" min="1" max="1000" v-model="counts[row.pk]"/>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
      <div slot="footer" class="text-center">
        <button @click="cancel_update" class="btn btn-blue-nb">Сохранить</button>
      </div>
    </modal>
  </div>
</template>

<script>
  import directions_point from '../api/directions-point'
  import * as action_types from '../store/action-types'
  import ResearchDisplay from './ResearchDisplay'
  import Modal from './Modal'
  import vSelect from 'vue-select'
  import TypeAhead from 'vue2-typeahead'
  import MKBField from '../fields/MKBField'
  import SelectFieldTitled from "../fields/SelectFieldTitled";

  export default {
    name: 'selected-researches',
    components: {
      SelectFieldTitled,
      ResearchDisplay,
      Modal,
      vSelect,
      TypeAhead,
      MKBField,
    },
    props: {
      simple: {
        type: Boolean,
        default: false,
      },
      researches: {
        type: Array,
        required: true
      },
      base: {
        type: Object
      },
      card_pk: {
        type: Number
      },
      operator: {
        type: Boolean,
        default: false
      },
      readonly: {
        type: Boolean,
        default: false
      },
      hide_diagnosis: {
        type: Boolean,
        default: false
      },
      ofname: {
        type: Number,
        default: -1
      },
      history_num: {
        type: String,
        default: ''
      },
      main_diagnosis: {
        type: String,
        default: ''
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
      clear_after_gen: {
        type: Boolean,
        default: false
      },
    },
    data() {
      return {
        diagnos: '',
        fin: -1,
        comments: {},
        localizations: {},
        counts: {},
        service_locations: {},
        need_update_comment: [],
        need_update_localization: [],
        need_update_service_location: [],
        hide_window_update: false,
        delayTime: 300,
        minChars: 1,
        limit: 11,
        selectFirst: true,
        vich_code: '',
        count: 1,
        discount: 0,
        purposes: [],
        direction_purpose: 'NONE',
        directions_count: '1',
      }
    },
    watch: {
      directions_count() {
        if (this.directions_count.trim() === '') {
          return
        }

        let nd = Number(this.directions_count) || 1

        if (nd < 1) {
          nd = 1
        }
        if (nd > 10) {
          nd = 10
        }

        this.directions_count = String(nd)
      },
      count() {
        this.count = Math.min(Math.max(parseInt(this.count) || 1, 1), 1000)
      },
      discount() {
        this.discount = Math.min(Math.max(parseInt(this.discount) || 0, 0), 100)
      },
      card_pk() {
        this.clear_fin()
      },
      base() {
        this.fin = -1
      },
      researches() {
        let comments = {}
        let service_locations = {}
        let localizations = {}
        let counts = {}
        this.need_update_comment = this.need_update_comment.filter(e => this.researches.indexOf(e) !== -1)
        this.need_update_localization = this.need_update_localization.filter(e => this.researches.indexOf(e) !== -1)
        this.need_update_service_location = this.need_update_service_location.filter(e => this.researches.indexOf(e) !== -1)
        let needShowWindow = false
        for (let pk of this.researches) {
          if (!this.comments[pk] && !this.localizations[pk] && !this.service_locations[pk]) {
            comments[pk] = ''
            if (pk in this.$store.getters.researches_obj) {
              let res = this.$store.getters.researches_obj[pk]
              if (res.comment_variants.length > 0) {
                comments[pk] = JSON.parse(JSON.stringify(res.comment_variants[0]))

                if (res.comment_variants.length > 1 && !this.need_update_comment.includes(pk)) {
                  this.need_update_comment.push(pk)
                  needShowWindow = true
                }
              }

              if (res.localizations && res.localizations.length > 0) {
                localizations[pk] = res.localizations[0]

                if (res.localizations.length > 1 && !this.need_update_localization.includes(pk)) {
                  this.need_update_localization.push(pk)
                  needShowWindow = true
                }
              }

              if (res.service_locations && res.service_locations.length > 0) {
                service_locations[pk] = res.service_locations[0]

                if (res.service_locations.length > 1 && !this.need_update_service_location.includes(pk)) {
                  this.need_update_service_location.push(pk)
                  needShowWindow = true
                }
              }
            }
            counts[pk] = 1
          } else {
            comments[pk] = this.comments[pk]
            localizations[pk] = this.localizations[pk]
            service_locations[pk] = this.service_locations[pk]
            counts[pk] = this.counts[pk]
          }
        }
        this.comments = comments
        this.localizations = localizations
        this.service_locations = service_locations
        this.counts = counts
        if (needShowWindow) {
          this.show_window()
          this.$forceUpdate()
        }
      },
      comments: {
        deep: true,
        handler() {
          for (let k of Object.keys(this.comments)) {
            if (this.comments[k] && this.comments[k].length > 40) {
              this.comments[k] = this.comments[k].substr(0, 40)
            }
          }
        }
      },
      diagnos() {
        if (/^[a-zA-Zа-яА-Я]\d.*/g.test(this.diagnos)) {
          this.diagnos = this.diagnos.toUpperCase()
          const replace = ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ',
            'ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э',
            'я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю']

          const search = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '\\[', '\\]',
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'',
            'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.']

          for (let i = 0; i < replace.length; i++) {
            let reg = new RegExp(replace[i], 'mig')
            this.diagnos = this.diagnos.replace(reg, function (a) {
              return a === a.toLowerCase() ? search[i] : search[i].toUpperCase()
            })
          }
        }
        this.$root.$emit('update_diagnos', this.diagnos)
      },
      fin() {
        this.$root.$emit('update_fin', this.fin)
      },
      direction_purpose_enabled: {
        immediate: true,
        handler() {
          if (this.direction_purpose_enabled) {
            this.load_direction_purposes();
          }
        },
      },
    },
    mounted() {
      this.$root.$on('researches-picker:clear_all' + this.kk, this.clear_all)
      this.$root.$on('researches-picker:update-comment' + this.kk, this.update_comment)
      this.$root.$on('patient-picker:select_card' + this.kk, this.clear_diagnos)
      if (this.initial_fin) {
        this.select_fin(this.initial_fin)
      }
    },
    methods: {
      update_comment(pk) {
        if (this.need_update_comment.indexOf(pk) === -1) {
          this.need_update_comment.push(pk)
        }
        this.show_window()
      },
      cancel_update() {
        this.need_update_comment = []
        this.need_update_localization = []
        this.need_update_service_location = []
        this.hide_window()
      },
      onHit(item) {
        this.diagnos = item.split(' ')[0] || ''
      },
      onHitVich(item) {
        this.vich_code = item.split(' ')[0] || ''
      },
      getResponse(resp) {
        return [...resp.data.data]
      },
      renderItems: (items) => items.map(i => `${i.code} ${i.title}`),
      get_def_diagnosis(fin) {
        fin = fin || this.fin
        return (this.main_diagnosis + ' ' + this.get_fin_obj(fin).default_diagnos).trim()
      },
      clear_diagnos() {
        this.diagnos = this.get_def_diagnosis()
        this.vich_code = ''
      },
      highlighting: (item, vue) => item.toString().replace(vue.query, `<b>${vue.query}</b>`),
      hide_window() {
        this.hide_window_update = true
        this.$refs.modal.$el.style.display = 'none'
      },
      show_window() {
        this.hide_window_update = false
        this.$refs.modal.$el.style.display = 'block'
      },
      researches_departments_simple() {
        let r = {}

        for (let pk of this.researches) {
          if (pk in this.$store.getters.researches_obj) {
            let res = this.$store.getters.researches_obj[pk]
            if (!(res.department_pk in r)) {
              r[res.department_pk] = []
            }
            r[res.department_pk].push(pk)
          }
        }
        return r
      },
      get_fin_obj(pk) {
        if (pk !== -1) {
          for (let f of this.base.fin_sources) {
            if (f.pk === pk)
              return f
          }
        }
        return {pk: -1, title: '', default_diagnos: ''}
      },
      select_fin(pk) {
        if (this.base.fin_sources.length === 1 && pk === -1) {
          pk = this.base.fin_sources[0].pk
        }
        const cfin = this.fin
        this.fin = pk
        this.count = 1
        this.discount = 0
        if (this.get_def_diagnosis(cfin) === this.diagnos || this.diagnos.trim() === '') {
          this.diagnos = this.get_def_diagnosis()
        }
      },
      clear_department(pk) {
        this.$root.$emit('researches-picker:deselect_department' + this.kk, pk)
      },
      generate(type) {
        if (this.diagnos === '' && this.current_fin !== 'Платно' && !this.pay_source) {
          $(this.$refs.d).focus()
          errmessage('Диагноз не указан', 'Если не требуется, то укажите прочерк ("-")')
          return
        }
        if (this.need_vich_code && this.vich_code === '') {
          $(this.$refs.v).focus()
          errmessage('Не указан код', 'Требуется код для направления на ВИЧ')
          return
        }
        this.$root.$emit('generate-directions', {
          type,
          card_pk: this.card_pk,
          fin_source_pk: this.fin,
          diagnos: this.diagnos.substr(0, 35),
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
          kk: this.kk,
          direction_purpose: this.direction_purpose,
          directions_count: Number(this.directions_count) || 1,
        })
      },
      clear_all() {
        this.$root.$emit('researches-picker:deselect_all' + this.kk)
        this.clear_fin()
        this.direction_purpose = 'NONE'
        this.directions_count = '1'
      },
      clear_fin() {
        this.select_fin(-1)
      },
      async load_direction_purposes() {
        await this.$store.dispatch(action_types.INC_LOADING)
        const {purposes} = await directions_point.getPurposes()
        this.purposes = purposes
        await this.$store.dispatch(action_types.DEC_LOADING)
      },
    },
    computed: {
      direction_purpose_enabled() {
        return this.$store.getters.modules.l2_direction_purpose
      },
      show_additions() {
        return this.researches.length > 0
      },
      current_fin() {
        return this.get_fin_obj(this.fin)
      },
      pay_source() {
        return this.current_fin.title.toLowerCase() === 'платно'
      },
      researches_departments() {
        let r = {}
        let deps = {
          '-2': {title: 'Консультации'},
          '-3': {title: 'Лечение'},
          '-4': {title: 'Стоматология'},
          '-5': {title: 'Стационар'},
          '-6': {title: 'Микробиология'}
        }
        for (let dep of this.$store.getters.allDepartments) {
          deps[dep.pk] = dep
        }

        for (let pk of this.researches) {
          if (pk in this.$store.getters.researches_obj) {
            let res = this.$store.getters.researches_obj[pk]
            let d = res.department_pk && !res.doc_refferal ? res.department_pk : -2
            if (!(d in r)) {
              r[d] = {
                pk: d,
                title: deps[d].title,
                researches: []
              }
            }
            r[d].researches.push({pk: pk, title: res.title})
          }
        }
        return r
      },
      need_vich_code() {
        for (let pk of this.researches) {
          if (pk in this.$store.getters.researches_obj && this.$store.getters.researches_obj[pk].need_vich_code) {
            return true
          }
        }
        return false
      },
      can_save() {
        return this.fin !== -1 && this.researches.length > 0 && this.card_pk !== -1
      },
      need_update_object() {
        let r = []
        const toUpd = [...this.need_update_comment]
        for (const pk of [...this.need_update_localization, ...this.need_update_service_location]) {
          if (!toUpd.includes(pk)) {
            toUpd.push(pk)
          }
        }
        for (let pk of toUpd) {
          if (pk in this.$store.getters.researches_obj) {
            let res = this.$store.getters.researches_obj[pk]
            r.push({
              pk: pk,
              title: res.title,
              options: res.comment_variants,
              localizations: res.localizations,
              service_locations: res.service_locations,
            })
          }
        }
        return r
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

  .top-picker /deep/ .form-control {
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

  .top-picker .vich-code /deep/ .form-control {
    width: 90px;
  }

  .top-picker /deep/ .input-group {
    border-radius: 0;
  }

  .top-picker /deep/ ul {
    width: auto;
    right: -250px;
    font-size: 13px;
  }

  .top-picker /deep/ ul li {
    overflow: hidden;
    text-overflow: ellipsis;
    padding: 2px .25rem;
    margin: 0 .2rem;

    a {
      padding: 2px 10px;
    }
  }

  .top-inner-select {
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

    &.disabled {
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
</style>
