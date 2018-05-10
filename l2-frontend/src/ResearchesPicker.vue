<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <button v-if="types.length > 1" class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
              style="width: 135px;text-align: left!important;border-radius: 0"><span class="caret"></span>
        {{selected_type.title}}
      </button>
      <ul v-if="types.length > 1" class="dropdown-menu">
        <li v-for="row in types" :value="row.pk" v-if="row.pk !== selected_type.pk">
          <a href="#" @click.prevent="select_type(row.pk)">{{row.title}}</a>
        </li>
      </ul>
      <button v-if="types.length === 1" class="btn btn-blue-nb btn-ell" type="button"
              style="width: 135px;border-radius: 0">
        {{selected_type.title}}
      </button>
      <div class="top-inner">
        <a href="#" @click.prevent="select_dep(row.pk)" class="top-inner-select" :class="{ active: row.pk === dep}"
           v-for="row in departments_of_type"><span>{{ row.title }}<span v-if="researches_selected_in_department(row.pk).length > 0"> ({{researches_selected_in_department(row.pk).length}})</span></span></a>
      </div>
    </div>
    <div class="content-picker" :class="{hidetemplates: hidetemplates}" v-if="researches_display.length > 0">
      <research-pick @click.native="select_research(row.pk)" class="research-select"
                     :class="{ active: research_selected(row.pk), highlight_search: highlight_search(row) }"
                     v-for="row in researches_display" :research="row"/>
    </div>
    <div class="content-none" v-else>
      Нет данных
    </div>
    <div class="bottom-picker" v-if="!hidetemplates" style="white-space: nowrap;">
      <div class="dropup" style="display: inline-block">
        <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                style="text-align: left!important;border-radius: 0"><span class="caret"></span>
          Загрузить шаблон
        </button>
        <ul class="dropdown-menu">
          <li v-for="row in templates" :value="row.pk">
            <a href="#" @click.prevent="load_template(row.pk)">{{row.title}}</a>
          </li>
        </ul>
      </div>
      <div style="display: flex;width: calc(100% - 164px);justify-content: flex-end;">
        <div id="founded-n" v-show="founded_n !== '' && search !== ''">
          <div style="font-size: 16px">{{founded_n}}</div>
        </div>
        <input type="text" placeholder="Поиск (Enter для быстрого выбора и очистки)" class="form-control"
               v-model="search" @keyup.enter="founded_select(true)" ref="fndsrc"
               @show="check_found_tip" @shown="check_found_tip"
               v-tippy="{html: '#founded-n', trigger: 'mouseenter focus input', reactive: true, arrow: true, animation : 'fade', duration : 0}"/>
        <button class="btn btn-blue-nb bottom-inner-btn" @click="founded_select" title="Быстрый выбор найденного"><span
          class="fa fa-circle"></span></button>
        <button class="btn btn-blue-nb bottom-inner-btn" @click="clear_search" title="Очистить поиск">
          <span>&times;</span></button>
      </div>
    </div>
  </div>
</template>

<script>
  import * as action_types from './store/action-types'
  import ResearchPick from './ResearchPick'

  export default {
    name: 'researches-picker',
    components: {ResearchPick},
    props: {
      value: {},
      autoselect: {
        default: 'directions'
      },
      hidetemplates: {
        default: false,
        type: Boolean
      },
      oneselect: {
        default: false,
        type: Boolean
      },
    },
    data() {
      return {
        type: '-1',
        dep: -1,
        template: -1,
        checked_researches: [],
        search: ''
      }
    },
    created() {
      let vm = this
      vm.$store.dispatch(action_types.INC_LOADING).then()

      this.$store.dispatch(action_types.GET_TEMPLATES).then().finally(() => {
        vm.$store.dispatch(action_types.DEC_LOADING).then()
      })

      vm.$store.dispatch(action_types.INC_LOADING).then()
      this.$store.dispatch(action_types.GET_RESEARCHES).then().finally(() => {
        vm.$store.dispatch(action_types.DEC_LOADING).then()
      })

      if (this.types.length === 0) {
        this.$store.watch(state => state.allTypes, (oldValue, newValue) => {
          this.checkType()
        })
      }

      if (this.templates.length === 0) {
        this.$store.watch(state => state.templates, (oldValue, newValue) => {
          this.check_template()
        })
      }

      this.checkType()
      this.check_template()

      this.$root.$on('researches-picker:deselect', this.deselect_research_ignore)
      this.$root.$on('researches-picker:deselect_department', this.deselect_department)
      this.$root.$on('researches-picker:deselect_all', this.clear)
      this.$root.$on('researches-picker:add_research', this.select_research_ignore)
    },
    watch: {
      types() {
        this.checkType()
      },
      templates() {
        this.check_template()
      },
      checked_researches() {
        if(this.oneselect) {
          this.$emit('input', this.checked_researches.length === 0? -1 : this.checked_researches[0])
          return;
        }
        this.$emit('input', this.checked_researches)
      },
      search() {
        this.check_found_tip()
      }
    },
    computed: {
      types() {
        let t = []
        for (let row of this.$store.getters.allTypes) {
          if (row.pk !== '0' && row.pk !== '1') {
            t.push(row)
          }
        }
        return t
      },
      selected_type() {
        for (let t of this.types) {
          if (t.pk === this.type) {
            return t
          }
        }
        return {title: 'Не выбран тип', pk: '-1'}
      },
      departments_of_type() {
        let r = []
        for (let row of this.$store.getters.allDepartments) {
          if (row.type === this.type) {
            r.push(row)
          }
        }
        return r
      },
      templates() {
        return this.$store.getters.templates
      },
      researches_display() {
        if (this.dep in this.$store.getters.researches) {
          return this.$store.getters.researches[this.dep]
        }
        return []
      },
      founded_n() {
        let r = 'Не найдено'
        let n = 0
        for (const row of this.researches_display) {
          if (this.highlight_search(row)) {
            n++
          }
        }
        if (n > 0) {
          r = `Найдено ${n}`
        }
        return r
      },
    },
    methods: {
      check_found_tip() {
        let el = this.$refs.fndsrc
        console.log(el._tippy)
        if (this.search === '' && '_tippy' in el && el._tippy.state.visible) {
          el._tippy.hide()
        }
      },
      select_type(pk) {
        this.type = pk
        this.checkType()
      },
      select_dep(pk) {
        this.dep = pk
      },
      checkType() {
        if (this.type === '-1' && this.types.length > 0) {
          this.type = JSON.parse(JSON.stringify(this.types[0].pk))
        }
        for (let row of this.departments_of_type) {
          if (this.dep === row.pk) {
            return
          }
        }
        this.dep = this.departments_of_type.length > 0 ? this.departments_of_type[0].pk : -1
      },
      check_template() {
        if (this.template === -1 && this.templates.length > 0) {
          this.template = JSON.parse(JSON.stringify(this.templates[0].pk))
        }
      },
      load_template(pk) {
        let last_dep = -1
        let last_type = -1
        for (let v of this.get_template(pk).values) {
          this.select_research_ignore(v)
          let d = this.research_data(v)
          last_dep = d.department_pk
          last_type = d.type
        }
        this.select_type(last_type)
        this.select_dep(last_dep)
      },
      get_template(pk) {
        for (let t of this.templates) {
          if (t.pk === pk) {
            return t
          }
        }
        return {title: 'Не выбран шаблон', pk: '-1', for_current_user: false, for_users_department: false, values: []}
      },
      select_research(pk) {
        if(this.oneselect) {
          this.checked_researches = [pk]
          return;
        }
        if (this.research_selected(pk)) {
          this.deselect_research_ignore(pk)
        } else {
          this.select_research_ignore(pk)
        }
      },
      select_research_ignore(pk) {
        if (!this.research_selected(pk)) {
          this.checked_researches.push(pk)
          let research = this.research_data(pk)
          if (this.autoselect === 'directions' && 'autoadd' in research) {
            for (let autoadd_pk of research.autoadd) {
              this.select_research_ignore(autoadd_pk)
            }
          }
        }
      },
      deselect_research_ignore(pk) {
        if (this.research_selected(pk)) {
          this.checked_researches = this.checked_researches.filter(item => item !== pk)
          let research = this.research_data(pk)
          if (this.autoselect === 'directions') {
            for (let addto_pk of research.addto) {
              this.deselect_research_ignore(addto_pk)
            }
          }
        }
      },
      deselect_department(pk) {
        for (let rpk of this.researches_selected_in_department(pk)) {
          this.deselect_research_ignore(rpk)
        }
      },
      clear() {
        this.checked_researches = []
      },
      research_selected(pk) {
        return this.checked_researches.indexOf(pk) !== -1
      },
      clear_search() {
        this.search = ''
      },
      founded_select(clear) {
        clear = clear || false
        for (const row of this.researches_display) {
          if (this.highlight_search(row)) {
            this.select_research_ignore(row.pk)
          }
        }
        if (clear) {
          this.clear_search()
        }
      },
      highlight_search(row) {
        const t = row.title.toLowerCase().trim()
        const ft = row.full_title.toLowerCase().trim()
        const c = row.code.toLowerCase().trim().replace('а', 'a').replace('в', 'b')
        const s = this.search.toLowerCase().trim()
        return s !== '' && (t.includes(s) || ft.includes(s) || c.startsWith(s.replace('а', 'a').replace('в', 'b')))
      },
      research_data(pk) {
        if (pk in this.$store.getters.researches_obj) {
          return this.$store.getters.researches_obj[pk]
        }
        return {}
      },
      researches_selected_in_department(pk) {
        let r = []
        for (let rpk of this.checked_researches) {
          let res = this.research_data(rpk)
          if (res.department_pk === pk) {
            r.push(rpk)
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

  .top-inner, .content-picker, .content-none {
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
    left: 135px;
    top: 0;
    right: 0;
    height: 34px;
    align-content: stretch;
    overflow: hidden;
  }

  .top-inner-select, .research-select {
    align-self: stretch;
    display: flex;
    align-items: center;
    padding: 1px 2px 1px;
    color: #000;
    background-color: #fff;
    text-decoration: none;
    transition: .15s linear all;
    cursor: pointer;
    flex: 1;
    margin: 0;
    font-size: 12px;
    min-width: 0;
  }

  .top-inner-select {
    background-color: #AAB2BD;
    color: #fff
  }

  .research-select {
    flex: 0 1 auto;
    width: 25%;
    height: 34px;
    border: 1px solid #6C7A89 !important;
    cursor: pointer;
    text-align: left;
    outline: transparent;
  }

  .top-inner-select.active, .research-select.active {
    background: #049372 !important;
    color: #fff;
  }

  .top-inner-select > span {
    display: block;
    text-overflow: ellipsis;
    overflow: hidden;
    word-break: keep-all;
    max-height: 2.2em;
    line-height: 1.1em;
  }

  .top-inner-select:hover {
    background-color: #434a54;
  }

  .research-select:hover {
    box-shadow: inset 0 0 8px rgba(0, 0, 0, .8) !important;
  }

  .highlight_search {
    background: #07f6bf;
    color: #000;
  }

  .content-picker, .content-none {
    position: absolute;
    top: 34px;
    &:not(.hidetemplates) {
      bottom: 34px;
    }
    &.hidetemplates {
      bottom: 0;
    }
    left: 0;
    right: 0;
    overflow-y: auto;
  }

  .bottom-picker {
    bottom: 0;
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    input {
      max-width: 350px;
      width: 100%;
      border-left: none;
      border-bottom: none;
      border-right: none;
      border-radius: 0;
    }
  }

  .bottom-inner-btn {
    width: auto;
    text-align: center;
    border-radius: 0;
  }
</style>
