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
    <div class="content-picker" v-if="researches_display.length > 0">
      <a href="#" @click.prevent="select_research(row.pk)" class="research-select"
         :class="{ active: research_selected(row.pk) }"
         v-for="row in researches_display" :title="row.title"><span>{{ row.title }}</span></a>
    </div>
    <div class="content-none" v-else>
      Нет данных
    </div>
    <div class="bottom-picker" style="white-space: nowrap;">
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
    </div>
  </div>
</template>

<script>
  import * as action_types from './store/action-types'

  export default {
    name: 'researches-picker',
    props: ['value'],
    data() {
      return {
        type: '-1',
        dep: -1,
        template: -1,
        checked_researches: []
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
        this.$emit('input', this.checked_researches)
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
    },
    methods: {
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
          for (let autoadd_pk of research.autoadd) {
            this.select_research_ignore(autoadd_pk)
          }
        }
      },
      deselect_research_ignore(pk) {
        if (this.research_selected(pk)) {
          this.checked_researches = this.checked_researches.filter(item => item !== pk)
          let research = this.research_data(pk)
          for (let addto_pk of research.addto) {
            this.deselect_research_ignore(addto_pk)
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
  }

  .top-inner-select.active, .research-select.active {
    background: #049372 !important;
    color: #fff;
  }

  .top-inner-select > span, .research-select span {
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
  }
</style>
