<template>
  <div class="root">
    <div class="top-editor">
      <div class="left">
        <div class="input-group">
          <span class="input-group-addon">Полное наименование</span>
          <input class="form-control" type="text" v-model="title">
        </div>
        <div class="input-group">
          <span class="input-group-addon">Краткое <small>(для создания направлений)</small></span>
          <input class="form-control" type="text" v-model="short_title">
        </div>
      </div>
      <div class="right">
        <div class="row" style="margin-right: 0;" v-if="department < -1">
          <div class="col-xs-6" style="padding-right: 0">
            <div class="input-group" style="margin-right: -1px">
              <span class="input-group-addon">Код (ОМС)</span>
              <input class="form-control f-code" type="text" v-model="code">
              <span class="input-group-addon">Код (внутр)</span>
              <input class="form-control f-code" type="text" v-model="internal_code">
            </div>
          </div>
          <div class="col-xs-6" style="padding-left: 0;padding-right: 0;margin-right: 0;">
            <div class="input-group">
              <span class="input-group-addon">Подраздел</span>
              <select class="form-control" v-model="site_type">
                <option :value="r.pk" v-for="r in ex_deps">{{r.title}}</option>
              </select>
            </div>
          </div>
        </div>
        <div class="input-group" v-else>
          <span class="input-group-addon">Код (ОМС)</span>
          <input class="form-control f-code" type="text" v-model="code">
          <span class="input-group-addon">Код (внутр)</span>
          <input class="form-control f-code" type="text" v-model="internal_code">
        </div>
        <div class="input-group">
          <label class="input-group-addon" style="height: 34px;text-align: left;">
            <input type="checkbox" v-model="hide"/> Скрытие исследования
          </label>
        </div>
      </div>
    </div>
    <div class="content-editor">
      <div class="input-group" style="margin-bottom: 5px">
        <span class="input-group-addon">Подготовка</span>
        <textarea class="form-control noresize" v-autosize="info" v-model="info"></textarea>
      </div>
      <div class="input-group">
        <span class="input-group-addon">Ёмкость для биоматериала</span>
        <select class="form-control" v-model="tube">
          <option :value="-1">Не выбрано</option>
          <option :value="t.pk" v-for="t in tubes">{{t.title}}</option>
        </select>
      </div>
    </div>

    <div class="footer-editor">
      <button @click="cancel" class="btn btn-blue-nb">Отмена</button>
      <button :disabled="!valid" @click="save" class="btn btn-blue-nb">Сохранить</button>
    </div>
  </div>
</template>

<script>
  import construct_point from '../api/construct-point'
  import * as action_types from '../store/action-types'
  import {mapGetters} from 'vuex'

  export default {
    name: 'microbiology-research-editor',
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
        internal_code: '',
        info: '',
        hide: false,
        cancel_do: false,
        loaded_pk: -2,
        site_type: null,
        groups: [],
        template_add_types: [
          {sep: ' ', title: 'Пробел'},
          {sep: ', ', title: 'Запятая и пробел'},
          {sep: '; ', title: 'Точка с запятой (;) и пробел'},
          {sep: '. ', title: 'Точка и пробел'},
          {sep: '\n', title: 'Перенос строки'},
        ],
        has_unsaved: false,
        f_templates_open: false,
        templates: [],
        opened_template_data: {},
        tube: -1,
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
      $(window).on('beforeunload', () => {
        if (this.has_unsaved && this.loaded_pk > -2 && !this.cancel_do)
          return 'Изменения, возможно, не сохранены. Вы уверены, что хотите покинуть страницу?'
      })
      this.$root.$on('hide_fte', () => this.f_templates_hide())
      this.$store.dispatch(action_types.GET_RESEARCHES)
    },
    computed: {
      fte() {
        return this.$store.getters.modules.l2_fast_templates
      },
      valid() {
        return this.tube !== -1 && this.norm_title.length > 0 && !this.cancel_do
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
      ex_dep() {
        return {
          '-2': 4,
          '-3': 5,
          '-4': 6,
          '-5': 7,
        }[this.department] || this.department
      },
      ex_deps() {
        return this.$store.getters.ex_dep[this.ex_dep] || []
      },
      ...mapGetters(['tubes']),
    },
    methods: {
      f_templates() {
        this.f_templates_open = true
      },
      f_templates_hide() {
        this.f_templates_open = false
      },
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
          lines: 3,
          field_type: 0,
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
        this.short_title = ''
        this.code = ''
        this.info = ''
        this.hide = false
        this.site_type = null
        this.tube = -1
        if (this.pk >= 0) {
          this.$store.dispatch(action_types.INC_LOADING)
          construct_point.researchDetails(this, 'pk').then(data => {
            this.title = data.title
            this.short_title = data.short_title
            this.code = data.code
            this.internal_code = data.internal_code
            this.info = data.info.replace(/<br\/>/g, '\n').replace(/<br>/g, '\n')
            this.hide = data.hide
            this.site_type = data.site_type
            this.loaded_pk = this.pk
            this.tube = data.tube
          }).finally(() => {
            this.$store.dispatch(action_types.DEC_LOADING)
          })
        } else {
          this.add_group()
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
        this.$store.dispatch(action_types.INC_LOADING)
        construct_point.updateResearch(this, ['pk', 'department', 'title', 'short_title', 'code', 'hide', 'site_type', 'internal_code', 'tube'], {
          info: this.info.replace(/\n/g, '<br/>').replace(/<br>/g, '<br/>')
        }).then(() => {
          this.has_unsaved = false
          okmessage('Сохранено')
          this.cancel()
        }).finally(() => {
          this.$store.dispatch(action_types.DEC_LOADING)
        })
      },
    }
  }
</script>

<style lang="scss" scoped>
  .modal-mask {
    align-items: stretch !important;
    justify-content: stretch !important;
  }

  /deep/ .panel-flt {
    margin: 41px;
    align-self: stretch !important;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  /deep/ .panel-body {
    flex: 1;
    padding: 0;
    height: calc(100% - 91px);
    min-height: 200px;
  }

  .top-editor {
    display: flex;
    flex: 0 0 68px;

    .left {
      flex: 0 0 45%
    }

    .right {
      flex: 0 0 55%
    }

    .left {
      border-right: 1px solid #96a0ad;
    }

    .input-group-addon {
      border-top: none;
      border-left: none;
      border-right: none;
      border-radius: 0;
    }

    .form-control {
      border-top: none;
      border-radius: 0;
    }

    .input-group > .form-control:last-child {
      border-right: none;
    }

    .f-code {
      padding: 6px;
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
      width: calc(100% - 530px);
    }

    &:nth-child(3), &:nth-child(4), &:nth-child(5), &:nth-child(6) {
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

    &:nth-child(3), &:nth-child(4) {
      width: 180px;
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

  .vc-collapse /deep/ .v-collapse-content {
    display: none;

    &.v-collapse-content-end {
      display: block;
    }
  }
</style>
