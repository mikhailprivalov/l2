<template>
  <div class="root">
    <div class="top-editor">
      <div class="left">
        <div class="input-group">
          <span class="input-group-addon">Полное наименование</span>
          <input type="text" class="form-control" v-model="title">
        </div>
        <div class="input-group">
          <span class="input-group-addon">Краткое <small>(при необходимости)</small></span>
          <input type="text" class="form-control" v-model="short_title">
        </div>
      </div>
      <div class="right">
        <div class="input-group">
          <span class="input-group-addon">Код</span>
          <input type="text" class="form-control" v-model="code">
        </div>
        <div class="input-group">
          <label class="input-group-addon" style="height: 34px;text-align: left;">
            <input type="checkbox" v-model="hide"/> Скрытие исследования
          </label>
        </div>
      </div>
    </div>
    <div class="content-editor">
      <div class="input-group">
        <span class="input-group-addon">Подготовка, кабинет</span>
        <input type="text" class="form-control" v-model="info">
      </div>
      <div v-for="group in ordered_groups" class="group">
        <div class="input-group">
          <span class="input-group-btn">
            <button class="btn btn-blue-nb lob" :disabled="is_first_group(group)" @click="dec_group_order(group)">
              <i class="glyphicon glyphicon-arrow-up"></i>
            </button>
          </span>
          <span class="input-group-btn">
            <button class="btn btn-blue-nb nob" :disabled="is_last_group(group)" @click="inc_group_order(group)">
              <i class="glyphicon glyphicon-arrow-down"></i>
            </button>
          </span>
          <span class="input-group-addon">Название группы</span>
          <input type="text" class="form-control" v-model="group.title">
        </div>
        <label>Отображать название <input v-model="group.show_title" type="checkbox"/></label><br/>
        <label>Скрыть группу <input v-model="group.hide" type="checkbox"/></label>
        <div>
          <strong>Поля ввода</strong>
        </div>
        <div v-for="row in ordered_fields(group)" class="field">
          <div class="field-inner">
            <div>
              <button class="btn btn-default btn-sm btn-block" :disabled="is_first_field(group, row)"
                      @click="dec_order(group, row)">
                <i class="glyphicon glyphicon-arrow-up"></i>
              </button>
              <button class="btn btn-default btn-sm btn-block" :disabled="is_last_field(group, row)"
                      @click="inc_order(group, row)">
                <i class="glyphicon glyphicon-arrow-down"></i>
              </button>
            </div>
            <div>
              <div class="input-group">
                <span class="input-group-addon">Название поля</span>
                <input type="text" class="form-control" v-model="row.title">
              </div>
              <div>
                <strong>Значение по умолчанию:</strong>
                <textarea v-model="row.default" :rows="row.lines" class="form-control" v-if="row.lines > 1"></textarea>
                <input v-model="row.default" class="form-control" v-else/>
              </div>
              <input-tag placeholder="Шаблоны быстр. ввода" :tags.sync="row.values_to_input" :addTagOnKeys="[13]"/>
            </div>
            <div>
              <label>
                <input type="checkbox" v-model="row.hide"/> скрыть поле
              </label>
              <label>
                 Число строк<br/>для ввода:<br/>
                <input class="form-control" type="number" min="1" v-model.int="row.lines"/>
              </label>
            </div>
          </div>
        </div>
        <div>
          <button class="btn btn-blue-nb" @click="add_field(group)">Добавить поле</button>
        </div>
      </div>
      <div>
        <button class="btn btn-blue-nb" @click="add_group">Добавить группу</button>
      </div>
    </div>
    <div class="footer-editor">
      <button class="btn btn-blue-nb" @click="cancel">Отмена</button>
      <button class="btn btn-blue-nb" :disabled="!valid" @click="save">Сохранить</button>
    </div>
  </div>
</template>

<script>
  import construct_point from '../api/construct-point'
  import * as action_types from '../store/action-types'
  import InputTag from 'vue-input-tag'

  export default {
    components: {
      InputTag
    },
    name: 'descriptive-research-editor',
    props: {
      pk: {
        type: Number,
        required: true
      },
      department: {
        type: Number,
        required: true
      },
    },
    created() {
      this.load()
    },
    data() {
      return {
        title: '',
        short_title: '',
        code: '',
        info: '',
        hide: false,
        cancel_do: false,
        loaded_pk: -2,
        groups: [],
      }
    },
    watch: {
      pk() {
        this.load()
      }
    },
    computed: {
      valid() {
        return this.norm_title.length > 0 && !this.cancel_do
      },
      norm_title() {
        return this.title.trim()
      },
      ordered_groups() {
        return this.groups.slice().sort(function (a, b) {
          return a.order === b.order ? 0 : +(a.order > b.order) || -1
        })
      },
      min_max_order_groups() {
        let min = 0
        let max = 0
        for (let row of this.groups) {
          if (min === 0) {
            min = row.order
          } else {
            min = Math.min(min, row.order)
          }
          max = Math.max(max, row.order)
        }
        return {min, max}
      },
    },
    methods: {
      min_max_order(group) {
        let min = 0
        let max = 0
        for (let row of group.fields) {
          if (min === 0) {
            min = row.order
          } else {
            min = Math.min(min, row.order)
          }
          max = Math.max(max, row.order)
        }
        return {min, max}
      },
      ordered_fields(group) {
        return group.fields.slice().sort(function (a, b) {
          return a.order === b.order ? 0 : +(a.order > b.order) || -1
        })
      },
      inc_group_order(row) {
        if (row.order === this.min_max_order_groups.max)
          return
        let next_row = this.find_group_by_order(row.order + 1)
        if (next_row) {
          next_row.order--
        }
        row.order++
      },
      dec_group_order(row) {
        if (row.order === this.min_max_order_groups.min)
          return
        let prev_row = this.find_group_by_order(row.order - 1)
        if (prev_row) {
          prev_row.order++
        }
        row.order--
      },
      inc_order(group, row) {
        if (row.order === this.min_max_order(group).max)
          return
        let next_row = this.find_by_order(group, row.order + 1)
        if (next_row) {
          next_row.order--
        }
        row.order++
      },
      dec_order(group, row) {
        if (row.order === this.min_max_order(group).min)
          return
        let prev_row = this.find_by_order(group, row.order - 1)
        if (prev_row) {
          prev_row.order++
        }
        row.order--
      },
      find_by_order(group, order) {
        for (let row of group.fields) {
          if (row.order === order) {
            return row
          }
        }
        return false
      },
      find_group_by_order(order) {
        for (let row of this.groups) {
          if (row.order === order) {
            return row
          }
        }
        return false
      },
      is_first_group(group) {
        return group.order === this.min_max_order_groups.min
      },
      is_last_group(group) {
        return group.order === this.min_max_order_groups.max
      },
      is_first_field(group, row) {
        return row.order === this.min_max_order(group).min
      },
      is_last_field(group, row) {
        return row.order === this.min_max_order(group).max
      },
      add_field(group) {
        let order = 0
        for (let row of group.fields) {
          order = Math.max(order, row.order)
        }
        group.fields.push({pk: -1, order: order + 1, title: '', default: '', values_to_input: [], hide: false, lines: 3})
      },
      add_group() {
        let order = 0
        for (let row of this.groups) {
          order = Math.max(order, row.order)
        }
        let g = {pk: -1, order: order + 1, title: '', fields: [], show_title: true, hide: false}
        this.add_field(g)
        this.groups.push(g)
      },
      load() {
        this.title = ''
        this.short_title = ''
        this.code = ''
        this.info = ''
        this.hide = false
        this.groups = []
        if (this.pk >= 0) {
          let vm = this
          vm.$store.dispatch(action_types.INC_LOADING).then()
          construct_point.researchDetails(vm.pk).then(data => {
            vm.title = data.title
            vm.short_title = data.short_title
            vm.code = data.code
            vm.info = data.info
            vm.hide = data.hide
            vm.loaded_pk = vm.pk
            vm.groups = data.groups
            if(vm.groups.length === 0) {
              vm.add_group()
            }
          }).finally(() => {
            vm.$store.dispatch(action_types.DEC_LOADING).then()
          })
        } else {
          this.add_group()
        }
      },
      cancel() {
        this.cancel_do = true
        this.$root.$emit('research-editor:cancel')
      },
      save() {
        let vm = this
        vm.$store.dispatch(action_types.INC_LOADING).then()
        construct_point.updateResearch(vm.pk, vm.department, vm.title, vm.short_title, vm.code, vm.info, vm.hide, vm.groups).then(() => {
          okmessage('Сохранено')
          this.cancel()
        }).finally(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      }
    }
  }
</script>

<style scoped lang="scss">
  .top-editor {
    display: flex;
    flex: 0 0 68px;

    .left, .right {
      flex: 0 0 50%
    }

    .left {
      border-right: 1px solid #96a0ad;
    }

    .input-group-addon {
      border-top: none;
      border-left: none;
      border-radius: 0;
    }

    .form-control {
      border-top: none;
      border-radius: 0;
    }

    .input-group > .form-control:last-child {
      border-right: none;
    }
  }

  .content-editor {
    height: 100%;
  }

  .footer-editor {
    flex: 0 0 34px;
    display: flex;
    justify-content: flex-end;
    background-color: #f4f4f4;

    .btn {
      border-radius: 0;
    }
  }

  .top-editor, .content-editor, .footer-editor {
    align-self: stretch;
  }

  .root {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    align-content: stretch;
  }

  .content-editor {
    padding: 5px;
    overflow-y: auto;
  }

  .group {
    padding: 5px;
    margin: 5px;
    border-radius: 5px;
    background: #f0f0f0;
  }

  .field {
    padding: 5px;
    margin: 5px;
    border-radius: 5px;
    background: #fff;
    color: #000;
  }

  .field-inner {
    display: flex;
    flex-direction: row;
    align-items: stretch;
  }

  .field-inner > div {
    align-self: stretch;
    textarea {
      resize: none;
    }

    &:nth-child(1) {
      flex: 0 0 35px;
      padding-right: 5px;
    }
    &:nth-child(2) {
      width: 100%;
    }
    &:nth-child(3) {
      width: 140px;
      padding-left: 5px;
      padding-right: 5px;
      white-space: nowrap;
      label {
        display: block;
        margin-bottom: 2px;
        width: 100%;
        input[type="number"] {
          width: 100%;
        }
      }
    }
  }

  .lob {
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
  }

  .nob {
    border-radius: 0;
  }
</style>
