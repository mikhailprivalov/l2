<template>
  <div ref="root" class="construct-root">
    <div class="construct-sidebar">
      <div class="sidebar-select">
        <select-picker-b style="height: 34px;" :options="departments_of_type" v-model="department"/>
      </div>
      <input class="form-control" style="padding-top: 7px;padding-bottom: 7px"
             placeholder="Фильтр по названию"/>
      <div class="sidebar-content" :class="{fcenter: researches_list.length === 0}">
        <div v-if="researches_list.length === 0">Ничего не найдено</div>
        <div class="research" v-for="row in researches_list" @click="open_editor(row.pk)">{{row.title}}</div>
      </div>
      <button class="btn btn-blue-nb sidebar-footer" :disabled="opened_id === -1" @click="open_editor(-1)"><i
        class="glyphicon glyphicon-plus"></i>
        Добавить
      </button>
    </div>
    <div class="construct-content">
      <descriptive-research-editor style="position: absolute;top: 0;right: 0;bottom: 0;left: 0;" v-if="opened_id > -2"
                                  :pk="opened_id" :department="department_int"/>
    </div>
  </div>
</template>

<script>
  import SelectPickerB from '../SelectPickerB'
  import DescriptiveResearchEditor from './DescriptiveResearchEditor'
  import researches_point from '../api/researches-point'
  import * as action_types from '../store/action-types'

  export default {
    components: {
      SelectPickerB,
      DescriptiveResearchEditor,
    },
    name: 'construct-descriptive',
    data() {
      return {
        department: '-1',
        departments: [],
        researches_list: [],
        opened_id: -2
      }
    },
    methods: {
      load_researches() {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        researches_point.getResearchesByDepartment(this.department).then(data => {
          vm.researches_list = data.researches
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      open_editor(pk) {
        this.opened_id = pk
      },
      cancel_edit() {
        this.opened_id = -2
        this.load_researches()
      }
    },
    created() {
      this.$parent.$on('research-editor:cancel', this.cancel_edit)
    },
    mounted() {
      let vm = this
      vm.departments = vm.$store.getters.allDepartments
      this.$store.watch(state => state.departments.all, (oldValue, newValue) => {
        vm.departments = vm.$store.getters.allDepartments
      })
    },
    watch: {
      departments() {
        if (this.department !== '-1' || this.departments_of_type.length === 0)
          return
        this.department = this.departments_of_type[0].value.toString()
      },
      department() {
        if (this.department === '-1')
          return
        this.load_researches()
      }
    },
    computed: {
      departments_of_type() {
        let d = []
        for (let row of this.departments) {
          if (row.type === '3') {
            d.push({label: row.title, value: row.pk})
          }
        }
        return d
      },
      department_int() {
        return parseInt(this.department)
      }
    }
  }
</script>

<style scoped lang="scss">
  .construct-root {
    display: flex;
    align-items: stretch;
    flex-direction: row;
    flex-wrap: nowrap;
    align-content: stretch;
    & > div {
      align-self: stretch;
    }
  }

  .construct-sidebar {
    width: 300px;
    border-right: 1px solid #b1b1b1;
    display: flex;
    flex-direction: column;

    .form-control {
      border-radius: 0;
      border-top: none;
      border-left: none;
      border-right: none;
    }
  }

  .construct-content {
    width: 100%;
    position: relative;
  }

  .sidebar-select /deep/ .btn {
    border-radius: 0;
    border-top: none;
    border-left: none;
    border-right: none;
    border-top: 1px solid #fff;
  }

  .sidebar-select, .sidebar-filter, .sidebar-footer {
    flex: 0 0 34px;
  }

  .sidebar-content {
    height: 100%;
  }

  .sidebar-footer {
    border-radius: 0;
    margin: 0;
  }

  .fcenter {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .research {
    background-image: linear-gradient(#1ad6fd, #1d62f0);
    color: #fff;
    padding: 5px;
    margin: 5px;
    border-radius: 5px;
    cursor: pointer;

    hr {

    }

    &:hover {
      box-shadow: 0 0 3px #1ad6fd;
    }
  }

  .research:not(:first-child) {
    margin-top: 0;
  }

  .research:last-child {
    margin-bottom: 0;
  }
</style>
