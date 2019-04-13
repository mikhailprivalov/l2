<template>
  <div style="height: 100%;width: 100%;position: relative" :class="[pay_source && 'pay_source']">
    <div :class="['top-picker', need_vich_code && 'need-vich-code']" v-if="!simple">
      <button class="btn btn-blue-nb top-inner-btn" @click="clear_diagnos" title="Очистить диагноз">
        <span>&times;</span>
      </button>
      <TypeAhead src="/api/mkb10?keyword=:keyword" :getResponse="getResponse" :onHit="onHit" ref="d" placeholder="Диагноз (МКБ 10)"
                 v-model="diagnos" maxlength="36" :delayTime="delayTime" :minChars="minChars"
                 :render="renderItems"
                 :limit="limit" :highlighting="highlighting" :selectFirst="selectFirst"
      />
      <div class="vich-code" v-if="need_vich_code">
        <TypeAhead src="/api/vich_code?keyword=:keyword" :getResponse="getResponse" :onHit="onHitVich" ref="v" placeholder="Код"
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
      <table class="table table-bordered table-condensed" style="table-layout: fixed">
        <colgroup>
          <col width="130">
          <col>
          <col width="101">
        </colgroup>
        <tbody>
        <tr v-if="researches.length === 0">
          <td colspan="3" class="text-center">Ничего не выбрано</td>
        </tr>
        <tr v-else v-for="(row, key) in researches_departments">
          <td>{{row.title}}</td>
          <td>
              <research-display v-for="(res, idx) in row.researches" :simple="simple"
                                :title="res.title" :pk="res.pk" :n="idx"
                                :nof="row.researches.length" :comment="comments[res.pk]"/>
          </td>
          <td>
            <a href="#" @click.prevent="clear_department(parseInt(key))">очистить</a>
          </td>
        </tr>
        <tr v-if="Object.keys(researches_departments).length > 1">
          <td colspan="2"></td>
          <td><a href="#" @click.prevent="clear_all">очистить всё</a></td>
        </tr>
        </tbody>
      </table>
    </div>
    <div class="bottom-picker-inputs" v-if="pay_source">
      <input v-model="count" placeholder="Количество" title="Количество" type="number" min="1" max="1000" class="form-control" />
      <input v-model="discount" placeholder="Скидка" title="Скидка" type="number" min="0" max="100" class="form-control" />
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
           v-show="need_update_comment.length > 0 && !hide_window_update">
      <span slot="header">Настройка коментариев для биоматериала</span>
      <div slot="body">
        <table class="table table-bordered table-responsive"
               style="margin-bottom: 0;width:auto;table-layout: fixed;background-color: #fff">
          <colgroup>
            <col width="300">
            <col width="300">
          </colgroup>
          <tbody>
          <tr v-for="row in need_update_object">
            <td>
              <div style="width:100%; overflow: hidden;text-overflow: ellipsis;" :title="row.title">{{row.title}}</div>
            </td>
            <td>
              <v-select :options="row.options" taggable v-model="comments[row.pk]"/>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
      <div slot="footer" class="text-center">
        <button class="btn btn-blue-nb" @click="cancel_update">Закрыть</button>
      </div>
    </modal>
  </div>
</template>

<script>
  import ResearchDisplay from './ui-cards/ResearchDisplay'
  import Modal from './ui-cards/Modal'
  import vSelect from 'vue-select'
  import TypeAhead from 'vue2-typeahead'

  export default {
    name: 'selected-researches',
    components: {
      ResearchDisplay,
      Modal,
      vSelect,
      TypeAhead,
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
    },
    data() {
      return {
        diagnos: '',
        fin: -1,
        comments: {},
        need_update_comment: [],
        hide_window_update: false,
        delayTime: 300,
        minChars: 1,
        limit: 11,
        selectFirst: true,
        vich_code: '',
        count: 1,
        discount: 0,
      }
    },
    watch: {
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
        let c = {}
        this.need_update_comment = this.need_update_comment.filter(e => this.researches.indexOf(e) !== -1)
        for (let pk of this.researches) {
          if (Object.keys(this.comments).indexOf(pk.toString()) === -1) {
            c[pk] = ''
            if (pk in this.$store.getters.researches_obj) {
              let res = this.$store.getters.researches_obj[pk]
              if (res.comment_variants.length > 0) {
                c[pk] = JSON.parse(JSON.stringify(res.comment_variants[0]))
              }
              if (res.comment_variants.length > 1) {
                this.need_update_comment.push(pk)
              }
            }
          } else {
            c[pk] = this.comments[pk]
          }
        }
        this.comments = c
      },
      need_update_comment() {
        if (this.need_update_comment.length > 0 && this.hide_window_update) {
          this.show_window()
        }
      },
      comments: {
        deep: true,
        handler() {
          for(let k of Object.keys(this.comments)) {
            if(this.comments[k] && this.comments[k].length > 9) {
              this.comments[k] = this.comments[k].substr(0, 9)
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
            'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '\\.']

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
      }
    },
    created() {
      this.$root.$on('researches-picker:clear_all', this.clear_all)
      this.$root.$on('researches-picker:update-comment', this.update_comment)
      this.$root.$on('patient-picker:select_card', this.clear_diagnos)
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
        this.hide_window()
      },
      onHit(item) {
        this.diagnos = item.split(' ')[0] || ''
      },
      onHitVich(item) {
        this.vich_code = item.split(' ')[0] || ''
      },
      getResponse(resp) {
        return [...resp.data.data];
      },
      renderItems: (items) => items.map(i => `${i.code} ${i.title}`),
      get_def_diagnosis(fin) {
        fin = fin || this.fin;
        return (this.main_diagnosis + ' ' + this.get_fin_obj(fin).default_diagnos).trim()
      },
      clear_diagnos() {
        this.diagnos = this.get_def_diagnosis()
        this.vich_code = '';
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
        if(pk !== -1) {
          for (let f of this.base.fin_sources) {
            if (f.pk === pk)
              return f
          }
        }
        return {pk: -1, title: "", default_diagnos: ""}
      },
      select_fin(pk) {
        if (this.base.fin_sources.length === 1 && pk === -1) {
          pk = this.base.fin_sources[0].pk;
        }
        const cfin = this.fin
        this.fin = pk
        this.count = 1;
        this.discount = 0;
        if(this.get_def_diagnosis(cfin) === this.diagnos || this.diagnos.trim() === ""){
          this.diagnos = this.get_def_diagnosis()
        }
      },
      clear_department(pk) {
        this.$root.$emit('researches-picker:deselect_department', pk)
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
          vich_code: this.need_vich_code ? this.vich_code : '',
          count: this.count,
          discount: this.discount,
          need_contract: this.pay_source
        })
      },
      clear_all() {
        this.$root.$emit('researches-picker:deselect_all')
        this.clear_fin()
      },
      clear_fin() {
        this.select_fin(-1)
      },
    },
    computed: {
      current_fin() {
        return this.get_fin_obj(this.fin);
      },
      pay_source() {
        return this.current_fin.title.toLowerCase() === 'платно';
      },
      researches_departments() {
        let r = {}
        let deps = {"-2": {title: "Консультации"}}
        for (let dep of this.$store.getters.allDepartments) {
          deps[dep.pk] = dep
        }

        for (let pk of this.researches) {
          if (pk in this.$store.getters.researches_obj) {
            let res = this.$store.getters.researches_obj[pk]
            let d = res.department_pk && !res.doc_refferal ? res.department_pk: -2;
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
            return true;
          }
        }
        return false;
      },
      can_save() {
        return this.fin !== -1 && this.researches.length > 0 && this.card_pk !== -1
      },
      need_update_object() {
        let r = []
        for (let pk of this.need_update_comment) {
          if (pk in this.$store.getters.researches_obj) {
            let res = this.$store.getters.researches_obj[pk]
            r.push({pk: pk, title: res.title, options: res.comment_variants})
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
    color: #000;
    background-color: #fff;
    text-decoration: none;
    cursor: pointer;
    flex: 1;
    margin: 0;
    font-size: 12px;
    min-width: 0;
  }

  .top-inner-select {
    background-color: #AAB2BD;
    color: #fff;
  }

  .research-select {
    flex: 0 1 auto;
    width: 25%;
    height: 34px;
    border: 1px solid #6C7A89 !important;
  }

  .top-inner-select.active {
    background: #049372 !important;
    color: #fff;
  }

  .top-inner-select.disabled {
    color: #fff;
    cursor: not-allowed;
    opacity: .8;
    background-color: rgba(255, 255, 255, .7) !important;
  }

  .top-inner-select span {
    display: block;
    text-overflow: ellipsis;
    overflow: hidden;
    word-break: keep-all;
    max-height: 2.2em;
    line-height: 1.1em;
    margin: 0 auto;
  }

  .top-inner-select:hover {
    background-color: #434a54;
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
</style>
