<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <input class="form-control" placeholder="Диагноз" v-model="diagnos"/>
      <div class="top-inner">
        <a href="#" @click.prevent="select_fin(row.pk)" class="top-inner-select" :class="{ active: row.pk === fin}"
           v-for="row in base.fin_sources"><span>{{ row.title }}</span></a>
      </div>
    </div>
    <div class="content-picker" style="margin: 5px">
      <table class="table table-bordered table-condensed">
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
            <research-display v-for="(res, idx) in row.researches"
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
    <div class="bottom-picker">
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

  export default {
    name: 'selected-researches',
    components: {
      ResearchDisplay,
      Modal,
      vSelect
    },
    props: {
      researches: {
        type: Array,
        reqired: true
      },
      base: {
        type: Object,
        reqired: true
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
      }
    },
    data() {
      return {
        diagnos: '',
        fin: -1,
        comments: {},
        need_update_comment: [],
        hide_window_update: false
      }
    },
    watch: {
      base() {
        this.fin = -1
      },
      researches() {
        let c = {}
        this.need_update_comment = this.need_update_comment.filter(e => this.researches.indexOf(e) !== -1)
        for (let pk of this.researches) {
          if (Object.keys(this.comments).indexOf(pk.toString()) !== -1) {
            c[pk] = this.comments[pk]
          } else {
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
      }
    },
    created() {
      this.$root.$on('researches-picker:clear_all', this.clear_all)
      this.$root.$on('researches-picker:update-comment', this.update_comment)
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
        let deps = {}
        for (let dep of this.$store.getters.allDepartments) {
          deps[dep.pk] = dep
        }

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
      select_fin(pk) {
        this.fin = pk
      },
      clear_department(pk) {
        this.$root.$emit('researches-picker:deselect_department', pk)
      },
      clear_all() {
        this.$root.$emit('researches-picker:deselect_all')
      },
      generate(type) {
        this.$root.$emit('generate-directions', {
          type,
          card_pk: this.card_pk,
          fin_source_pk: this.fin,
          diagnos: this.diagnos,
          base: this.base,
          researches: this.researches_departments_simple(),
          operator: this.operator,
          ofname: this.ofname,
          history_num: this.history_num,
          comments: this.comments
        })
      },
      clear_all() {
        this.$root.$emit('researches-picker:deselect_all')
        this.fin = -1
      },
    },
    computed: {
      researches_departments() {
        let r = {}
        let deps = {}
        for (let dep of this.$store.getters.allDepartments) {
          deps[dep.pk] = dep
        }

        for (let pk of this.researches) {
          if (pk in this.$store.getters.researches_obj) {
            let res = this.$store.getters.researches_obj[pk]
            if (!(res.department_pk in r)) {
              r[res.department_pk] = {
                pk: res.department_pk,
                title: deps[res.department_pk].title,
                researches: []
              }
            }
            r[res.department_pk].researches.push({pk: pk, title: res.full_title})
          }
        }
        return r
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

<style scoped>
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

  .top-inner {
    position: absolute;
    left: 180px;
    top: 0;
    right: 0;
    height: 34px;
    align-content: stretch;
    overflow: hidden;
  }

  .top-picker .form-control {
    width: 180px;
    border-radius: 0;
    border: none;
    border-bottom: 1px solid #AAB2BD;
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
    top: 34px;
    bottom: 34px;
    left: 0;
    right: 0;
    overflow-y: auto;
  }

  .bottom-picker {
    bottom: 0;
    align-content: stretch;
    overflow: hidden;
  }

  .bottom-picker .top-inner-select span {
    margin: 0 auto;
    text-align: center;
  }
</style>
