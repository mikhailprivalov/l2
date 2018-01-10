<template>
  <div style="height: 100%;width: 100%;position: relative">
    <div class="top-picker">
      <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
              style="width: 135px;text-align: left!important;border-radius: 0"><span class="caret"></span>
        {{selected_type.title}}
      </button>
      <ul class="dropdown-menu">
        <li v-for="row in types" :value="row.pk" v-if="row.pk !== selected_type.pk">
          <a href="#" @click.prevent="select_type(row.pk)">{{row.title}}</a>
        </li>
      </ul>
      <div class="top-inner">
        <a href="#" @click.prevent="select_dep(row.pk)" class="top-inner-select" :class="{ active: row.pk === dep}"
           v-for="row in departments_of_type"><span>{{ row.title }}</span></a>
      </div>
    </div>
    <div class="content-picker" v-if="researches_display.length > 0">
        <a href="#" @click.prevent="select_research(row.pk)" class="research-select" :class="{ active: research_selected(row.pk) }"
           v-for="row in researches_display" :title="row.title"><span>{{ row.title }}</span></a>
    </div>
    <div class="content-none" v-else>
      Нет данных
    </div>
    <div class="bottom-picker" style="white-space: nowrap;">
      <div class="dropup" style="display: inline-block">
        <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
                style="text-align: left!important;border-radius: 0"><span class="caret"></span>
          {{selected_template.title}}
        </button>
        <ul class="dropdown-menu">
          <li v-for="row in templates" :value="row.pk" v-if="row.pk !== selected_template.pk">
            <a href="#" @click.prevent="select_template(row.pk)">{{row.title}}</a>
          </li>
        </ul>
      </div>
      <button class="btn btn-blue-nb btn-ell dropdown-toggle" type="button" data-toggle="dropdown"
              style="text-align: left!important;border-radius: 0" @click="load_template">
        Загрузить шаблон
      </button>
    </div>
  </div>
</template>

<script>
  import * as action_types from './store/action-types'

  export default {
    name: 'researches-picker',
    data() {
      return {
        type: '-1',
        dep: -1,
        template: -1,
        checked_researches: []
      }
    },
    created() {
      this.$store.dispatch(action_types.GET_TEMPLATES).then()
      this.$store.dispatch(action_types.GET_RESEARCHES).then()

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
    },
    watch: {
      types() {
        this.checkType()
      },
      templates() {
        this.check_template()
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
      selected_template() {
        for (let t of this.templates) {
          if (t.pk === this.template) {
            return t
          }
        }
        return {title: 'Не выбран шаблон', pk: '-1', for_current_user: false, for_users_department: false, values: []}
      },
      researches_display() {
        if(this.dep in this.$store.getters.researches){
          return this.$store.getters.researches[this.dep]
        }
        return []
      },
      researches_obj() {
        let o = {}
        let researches = this.$store.getters.researches
        for(let k in researches){
          if(researches.hasOwnProperty(k)) {
            for(let r of researches[k]){
              o[r.pk] = r
            }
          }
        }
        return o
      }
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
      select_template(pk) {
        this.template = pk
      },
      select_research(pk) {
        if(this.research_selected(pk)){
          this.checked_researches = this.checked_researches.filter(item => item !== pk)
        } else {
          this.checked_researches.push(pk)
        }
      },
      research_selected(pk) {
        return this.checked_researches.indexOf(pk) !== -1
      },
      research_data(pk) {
        if(pk in this.researches_obj){
          return this.researches_obj[pk]
        }
        return {}
      },
      load_template() {
        let last_dep = -1
        let last_type = -1
        for(let v of this.selected_template.values) {
          if(!this.research_selected(v)) {
            this.select_research(v)
          }
          let d = this.research_data(v)
          last_dep = d.department_pk
          last_type = d.type
        }
        this.select_type(last_type)
        this.select_dep(last_dep)
      },
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
    background: #049372;
    color: #fff;
  }

  .top-inner-select span, .research-select span {
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
