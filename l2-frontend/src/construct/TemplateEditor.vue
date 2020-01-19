<template>
  <div class="root">
    <div class="top-editor">
      <div class="input-group" style="width: 100%;">
        <span class="input-group-addon">Название</span>
        <input type="text" class="form-control" v-model="title">
      </div>
      <div class="input-group">
        <label class="input-group-addon" style="height: 34px;text-align: left;">
          <input type="checkbox" v-model="global_template"/> {{global_template ? "Global" : "Searchable"}}
        </label>
      </div>
    </div>
    <div class="content-editor">
      <div class="row" style="height: 100%">
        <div class="col-xs-6" style="height: 100%">
          <researches-picker v-model="researches" autoselect="none" :hidetemplates="true" v-if="researches !== null" />
        </div>
        <div class="col-xs-6" style="height: 100%">
          <selected-researches :researches="researches || []" :simple="true" />
        </div>
      </div>
    </div>
    <div class="footer-editor">
      <button class="btn btn-blue-nb" @click="cancel">Отмена</button>
      <button class="btn btn-blue-nb" :disabled="!valid" @click="save">Сохранить</button>
    </div>
  </div>
</template>

<script>
  import ResearchesPicker from '../ui-cards/ResearchesPicker'
  import SelectedResearches from '../ui-cards/SelectedResearches'
  import construct_point from '../api/construct-point'
  import * as action_types from '../store/action-types'

  export default {
    name: 'template-editor',
    components: {
      ResearchesPicker,
      SelectedResearches,
    },
    props: {
      pk: {
        type: Number,
        required: true
      },
      global_template_p: {
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
        cancel_do: false,
        loaded_pk: -2,
        researches: null,
        has_unsaved: false,
        global_template: false,
      }
    },
    watch: {
      pk() {
        this.load()
      },
      loaded_pk(n) {
        this.has_unsaved = false
      },
      groups: {
        handler(n, o) {
          if (o && o.length > 0) {
            this.has_unsaved = true
          }
        },
        deep: true
      }
    },
    mounted() {
      let vm = this
      $(window).on('beforeunload', function () {
        if (vm.has_unsaved && vm.loaded_pk > -2 && !vm.cancel_do)
          return 'Изменения, возможно, не сохранены. Вы уверены, что хотите покинуть страницу?'
      })
    },
    computed: {
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
      valid() {
        return this.norm_title.length > 0 && this.researches && this.researches.length > 0
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
      is_first_in_template(i) {
        return i === 0
      },
      is_last_in_template(row, i) {
        return i === row.values_to_input.length - 1
      },
      up_template(row, i) {
        if (this.is_first_in_template(i))
          return
        let values = JSON.parse(JSON.stringify(row.values_to_input));
        [values[i - 1], values[i]] = [values[i], values[i - 1]]
        row.values_to_input = values
      },
      down_template(row, i) {
        if (this.is_last_in_template(row, i))
          return
        let values = JSON.parse(JSON.stringify(row.values_to_input));
        [values[i + 1], values[i]] = [values[i], values[i + 1]]
        row.values_to_input = values
      },
      remove_template(row, i) {
        if (row.values_to_input.length - 1 < i)
          return
        row.values_to_input.splice(i, 1)
      },
      add_template_value(row) {
        if (row.new_value === '')
          return
        row.values_to_input.push(row.new_value)
        row.new_value = ''
      },
      drag(row, ev) {
        // console.log(row, ev)
      },
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
        group.fields.push({
          pk: -1,
          order: order + 1,
          title: '',
          default: '',
          values_to_input: [],
          new_value: '',
          hide: false,
          lines: 3
        })
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
        this.researches = null
        this.global_template = this.global_template_p === 1
        if (this.pk >= 0) {
          let vm = this
          vm.$store.dispatch(action_types.INC_LOADING).then()
          fetch('/api/get-template?pk=' + this.pk).then(r => r.json()).then(data => {
            vm.title = data.title
            vm.researches = data.researches
            vm.global_template = data.global_template
          }).finally(() => {
            vm.$store.dispatch(action_types.DEC_LOADING).then()
          })
        } else {
          this.researches = []
        }
      },
      cancel() {
        if (this.has_unsaved && !confirm('Изменения, возможно, не сохранены. Вы уверены, что хотите отменить редактирование?')) {
          return
        }
        this.cancel_do = true
        this.$root.$emit('research-editor:cancel')
      },
      save() {
        this.$store.dispatch(action_types.INC_LOADING).then()
        construct_point.updateTemplate(this, ['pk', 'title', 'researches', 'global_template']).then(() => {
          this.has_unsaved = false
          okmessage('Сохранено')
          this.cancel()
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING).then()
        })
      }
    }
  }
</script>

<style>
  body {
    overflow-x: hidden;
  }
</style>

<style scoped lang="scss">
  .top-editor {
    display: flex;
    flex: 0 0 43px;

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
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 34px;
    display: flex;
    justify-content: flex-end;
    background-color: #f4f4f4;

    .btn {
      border-radius: 0;
    }
  }

  .top-editor, .content-editor {
    align-self: stretch;
  }

  .root {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    align-content: stretch;
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

  /deep/ .v-collapse-content-end {
    max-height: 10000px !important;
  }
</style>
