<template>
  <div ref="root" class="construct-root">
    <div class="construct-sidebar" v-show="opened_id === -2">
      <div class="sidebar-select">
        <select-picker-m style="height: 34px;" :options="departments_of_type" v-model="department"
                         v-if="departments_of_type.length > 0"/>
      </div>
      <input class="form-control" v-model="title_filter" style="padding-top: 7px;padding-bottom: 7px"
             placeholder="Фильтр по названию"/>
      <div class="sidebar-content" :class="{fcenter: researches_list_filtered.length === 0}">
        <div v-if="researches_list_filtered.length === 0">Не найдено</div>
        <div class="research" :class="{rhide: row.hide}"
             v-for="row in researches_list_filtered"
             @click="open_editor(row.pk)">{{row.title}}
        </div>
      </div>
      <button class="btn btn-blue-nb sidebar-footer" @click="open_editor(-1)">
        <i class="glyphicon glyphicon-plus"></i>
        Добавить
      </button>
    </div>
    <div class="construct-content" v-if="parseInt(department) <= -500 && parseInt(department) > -600">
      <stationar-form-editor style="position: absolute;top: 0;right: 0;bottom: 0;left: 0;" v-if="opened_id > -2"
                             :pk="opened_id" :department="department_int"/>
    </div>
    <div class="construct-content" v-else-if="department !== '-6'">
      <paraclinic-research-editor style="position: absolute;top: 0;right: 0;bottom: 0;left: 0;" v-if="opened_id > -2"
                                  :pk="opened_id" :department="department_int"/>
    </div>
    <div class="construct-content" v-else>
      <microbiology-research-editor :department="department_int" :pk="opened_id"
                                    style="position: absolute;top: 0;right: 0;bottom: 0;left: 0;"
                                    v-if="opened_id > -2"/>
    </div>
  </div>
</template>

<script>
    import SelectPickerM from '../fields/SelectPickerM'
    import ParaclinicResearchEditor from './ParaclinicResearchEditor'
    import MicrobiologyResearchEditor from './MicrobiologyResearchEditor'
    import researches_point from '../api/researches-point'
    import {mapGetters} from 'vuex'
    import * as action_types from '../store/action-types'
    import StationarFormEditor from './StationarFormEditor'

    export default {
        components: {
            StationarFormEditor,
            SelectPickerM,
            ParaclinicResearchEditor,
            MicrobiologyResearchEditor,
        },
        name: 'construct-paraclinic',
        data() {
            return {
                department: '-1',
                // departments: [],
                researches_list: [],
                departments_of_type: [],
                opened_id: -2,
                title_filter: ''
            }
        },
        methods: {
            load_researches() {
                let vm = this
                vm.$store.dispatch(action_types.INC_LOADING).then()
                researches_point.getResearchesByDepartment(this, 'department').then(data => {
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
            },
            update_deps() {
                let d = []
                if (Object.keys(this.modules).length > 0) {
                    for (let row of this.departments) {
                        if (row.type === '3') {
                            d.push({label: row.title, value: row.pk})
                            if (row.pk.toString() === this.$store.getters.user_data.department.pk.toString() && this.department === '-1') {
                                this.department = row.pk.toString()
                            }
                        }
                    }

                    if (this.modules.consults_module) {
                        d.push({value: -2, label: 'Консультации'})
                    }

                    if (this.modules.l2_treatment) {
                        d.push({value: -3, label: 'Лечение'})
                    }

                    if (this.modules.l2_stom) {
                        d.push({value: -4, label: 'Стоматология'})
                    }

                    if (this.modules.l2_microbiology) {
                        d.push({value: -6, label: 'Микробиология'})
                    }

                    if (this.modules.l2_hosp && this.can_edit_stationar) {
                        d.push({value: -5, label: 'Стационар'})
                        d.push({value: -500, label: '– Первичный прием'})
                        d.push({value: -501, label: '– Дневник'})
                        d.push({value: -502, label: '– ВК'})
                        d.push({value: -503, label: '– Операции'})
                        d.push({value: -504, label: '– Фармакотерапия'})
                        d.push({value: -505, label: '– Физиотерапия'})
                        d.push({value: -506, label: '– Эпикриз'})
                        d.push({value: -506, label: '– Выписка'})
                    }
                }

                this.departments_of_type = d

                this.set_dep()
            },
            set_dep(deps) {
                if (this.department !== '-1' || !deps || deps.length === 0
                    || !this.$store.getters.user_data.department)
                    return
                for (let row of deps) {
                    if (row.value === this.$store.getters.user_data.department.pk) {
                        this.department = row.value.toString()
                        return
                    }
                }
                this.department = deps[0].value.toString()
            }
        },
        created() {
            this.$parent.$on('research-editor:cancel', this.cancel_edit)
        },
        mounted() {
            this.$store.watch(state => state.user.data, (oldValue, newValue) => {
                this.update_deps()
            })
            this.update_deps()
        },
        watch: {
            department: {
                handler() {
                    if (this.department === '-1')
                        return
                    this.load_researches()
                },
                immediate: true,
            },
            modules: {
                handler() {
                    this.update_deps()
                },
                deep: true,
                immediate: true,
            },
            departments: {
                handler() {
                    this.update_deps()
                },
                deep: true,
                immediate: true,
            },
        },
        computed: {
            department_int() {
                return parseInt(this.department)
            },
            researches_list_filtered() {
                return this.researches_list.filter(row => row.title.trim().toLowerCase().indexOf(this.title_filter.trim().toLowerCase()) >= 0)
            },
            ...mapGetters({
                departments: 'allDepartments',
                modules: 'modules',
            }),
            can_edit_stationar() {
                for (let g of (this.$store.getters.user_data.groups || [])) {
                    if (g === 'Редактирование стационара') {
                        return true
                    }
                }
                return false
            },
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
    width: 350px;
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
    overflow-y: auto;
    background-color: hsla(30, 3%, 97%, 1);
  }

  .sidebar-content:not(.fcenter) {
    padding-bottom: 10px;
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
    background-color: #fff;
    padding: 5px;
    margin: 10px;
    border-radius: 4px;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    transition: all .2s cubic-bezier(.25, .8, .25, 1);
    position: relative;

    &.rhide {
      background-image: linear-gradient(#6C7A89, #56616c);
      color: #fff;
    }

    hr {

    }

    &:hover {
      box-shadow: 0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22);
      z-index: 1;
      transform: scale(1.008);
    }
  }

  .research:not(:first-child) {
    margin-top: 0;
  }

  .research:last-child {
    margin-bottom: 0;
  }
</style>
