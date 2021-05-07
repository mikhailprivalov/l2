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
import ResearchesPicker from '../ui-cards/ResearchesPicker.vue';
import SelectedResearches from '../ui-cards/SelectedResearches.vue';
import construct_point from '../api/construct-point';
import * as actions from '../store/action-types';

export default {
  name: 'template-editor',
  components: {
    ResearchesPicker,
    SelectedResearches,
  },
  props: {
    pk: {
      type: Number,
      required: true,
    },
    global_template_p: {
      type: Number,
      required: true,
    },
  },
  created() {
    this.load();
  },
  data() {
    return {
      title: '',
      cancel_do: false,
      loaded_pk: -2,
      researches: null,
      has_unsaved: false,
      global_template: false,
    };
  },
  watch: {
    pk() {
      this.load();
    },
    loaded_pk() {
      this.has_unsaved = false;
    },
    groups: {
      handler(n, o) {
        if (o && o.length > 0) {
          this.has_unsaved = true;
        }
      },
      deep: true,
    },
  },
  mounted() {
    window.$(window).on('beforeunload', () => {
      if (this.has_unsaved && this.loaded_pk > -2 && !this.cancel_do) {
        return 'Изменения, возможно, не сохранены. Вы уверены, что хотите покинуть страницу?';
      }

      return undefined;
    });
  },
  computed: {
    researches_departments() {
      const r = {};
      const deps = { '-2': { title: 'Консультации' } };
      for (const dep of this.$store.getters.allDepartments) {
        deps[dep.pk] = dep;
      }

      for (const pk of this.researches) {
        if (pk in this.$store.getters.researches_obj) {
          const res = this.$store.getters.researches_obj[pk];
          const d = res.department_pk && !res.doc_refferal ? res.department_pk : -2;
          if (!(d in r)) {
            r[d] = {
              pk: d,
              title: deps[d].title,
              researches: [],
            };
          }
          r[d].researches.push({ pk, title: res.title });
        }
      }
      return r;
    },
    valid() {
      return this.norm_title.length > 0 && this.researches && this.researches.length > 0;
    },
    norm_title() {
      return this.title.trim();
    },
    ordered_groups() {
      return this.groups.slice().sort((a, b) => (a.order === b.order ? 0 : +(a.order > b.order) || -1));
    },
    min_max_order_groups() {
      let min = 0;
      let max = 0;
      for (const row of this.groups) {
        if (min === 0) {
          min = row.order;
        } else {
          min = Math.min(min, row.order);
        }
        max = Math.max(max, row.order);
      }
      return { min, max };
    },
  },
  methods: {
    is_first_in_template(i) {
      return i === 0;
    },
    is_last_in_template(row, i) {
      return i === row.values_to_input.length - 1;
    },
    up_template(row, i) {
      if (this.is_first_in_template(i)) return;
      const values = JSON.parse(JSON.stringify(row.values_to_input));
      [values[i - 1], values[i]] = [values[i], values[i - 1]];
      // eslint-disable-next-line no-param-reassign
      row.values_to_input = values;
    },
    down_template(row, i) {
      if (this.is_last_in_template(row, i)) return;
      const values = JSON.parse(JSON.stringify(row.values_to_input));
      [values[i + 1], values[i]] = [values[i], values[i + 1]];
      // eslint-disable-next-line no-param-reassign
      row.values_to_input = values;
    },
    remove_template(row, i) {
      if (row.values_to_input.length - 1 < i) return;
      row.values_to_input.splice(i, 1);
    },
    add_template_value(row) {
      if (row.new_value === '') return;
      row.values_to_input.push(row.new_value);
      // eslint-disable-next-line no-param-reassign
      row.new_value = '';
    },
    drag() {
      // console.log(row, ev)
    },
    min_max_order(group) {
      let min = 0;
      let max = 0;
      for (const row of group.fields) {
        if (min === 0) {
          min = row.order;
        } else {
          min = Math.min(min, row.order);
        }
        max = Math.max(max, row.order);
      }
      return { min, max };
    },
    ordered_fields(group) {
      return group.fields.slice().sort((a, b) => (a.order === b.order ? 0 : +(a.order > b.order) || -1));
    },
    inc_group_order(row) {
      if (row.order === this.min_max_order_groups.max) return;
      const next_row = this.find_group_by_order(row.order + 1);
      if (next_row) {
        next_row.order--;
      }
      // eslint-disable-next-line no-param-reassign
      row.order++;
    },
    dec_group_order(row) {
      if (row.order === this.min_max_order_groups.min) return;
      const prev_row = this.find_group_by_order(row.order - 1);
      if (prev_row) {
        prev_row.order++;
      }
      // eslint-disable-next-line no-param-reassign
      row.order--;
    },
    inc_order(group, row) {
      if (row.order === this.min_max_order(group).max) return;
      const next_row = this.find_by_order(group, row.order + 1);
      if (next_row) {
        next_row.order--;
      }
      // eslint-disable-next-line no-param-reassign
      row.order++;
    },
    dec_order(group, row) {
      if (row.order === this.min_max_order(group).min) return;
      const prev_row = this.find_by_order(group, row.order - 1);
      if (prev_row) {
        prev_row.order++;
      }
      // eslint-disable-next-line no-param-reassign
      row.order--;
    },
    find_by_order(group, order) {
      for (const row of group.fields) {
        if (row.order === order) {
          return row;
        }
      }
      return false;
    },
    find_group_by_order(order) {
      for (const row of this.groups) {
        if (row.order === order) {
          return row;
        }
      }
      return false;
    },
    is_first_group(group) {
      return group.order === this.min_max_order_groups.min;
    },
    is_last_group(group) {
      return group.order === this.min_max_order_groups.max;
    },
    is_first_field(group, row) {
      return row.order === this.min_max_order(group).min;
    },
    is_last_field(group, row) {
      return row.order === this.min_max_order(group).max;
    },
    add_field(group) {
      let order = 0;
      for (const row of group.fields) {
        order = Math.max(order, row.order);
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
      });
    },
    add_group() {
      let order = 0;
      for (const row of this.groups) {
        order = Math.max(order, row.order);
      }
      const g = {
        pk: -1, order: order + 1, title: '', fields: [], show_title: true, hide: false,
      };
      this.add_field(g);
      this.groups.push(g);
    },
    load() {
      this.title = '';
      this.researches = null;
      this.global_template = this.global_template_p === 1;
      if (this.pk >= 0) {
        this.$store.dispatch(actions.INC_LOADING);
        fetch(`/api/get-template?pk=${this.pk}`).then((r) => r.json()).then((data) => {
          this.title = data.title;
          this.researches = data.researches;
          this.global_template = data.global_template;
        }).finally(() => {
          this.$store.dispatch(actions.DEC_LOADING);
        });
      } else {
        this.researches = [];
      }
    },
    cancel() {
      // eslint-disable-next-line no-restricted-globals,no-alert
      if (this.has_unsaved && !confirm('Изменения, возможно, не сохранены. Вы уверены, что хотите отменить редактирование?')) {
        return;
      }
      this.cancel_do = true;
      this.$root.$emit('research-editor:cancel');
    },
    save() {
      this.$store.dispatch(actions.INC_LOADING);
      construct_point.updateTemplate(this, ['pk', 'title', 'researches', 'global_template']).then(() => {
        this.has_unsaved = false;
        window.okmessage('Сохранено');
        this.cancel();
      }).finally(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
  },
};
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

  ::v-deep .v-collapse-content-end {
    max-height: 10000px !important;
  }
</style>
