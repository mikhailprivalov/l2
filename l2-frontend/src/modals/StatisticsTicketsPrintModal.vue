<template>
  <div class="modal fade" tabindex="-1">
    <div class="modal-dialog" style="max-width: 800px;width: 100%">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
          <h4 class="modal-title">Печать статталонов</h4>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-xs-5 text-right">
              <date-selector :date_type.sync="date_type" :values.sync="values"/>
              <label style="width: 100%;text-align: left;">
                Источник финансирования:
                <select v-model="fin" class="form-control">
                  <optgroup :label="b.title" v-for="b in bases" :key="b.pk">
                    <option v-for="f in b.fin_sources.filter(x => !x.hide)" :key="f.pk" :value="f.pk">
                      {{b.title}} – {{f.title}}
                    </option>
                  </optgroup>
                </select>
              </label>
            </div>
            <div class="col-xs-7">
              <select-picker :val="user" :options="users_list" :func="change_user"
                             :disabled="dep !== '-1' && dep !== ''" />
              <div v-if="deps_list.length > 0">
                <div class="text-center">или</div>
                <select-picker :val="dep" :options="deps_list" :func="change_dep"
                               :disabled="user !== '-1' && user !== ''" />
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <div class="row">
            <div class="col-xs-3"></div>
            <div class="col-xs-6">
              <button type="button" @click="make_report"
                      :disabled="(user === '-1' || user === '') && dep === '-1'"
                      class="btn btn-primary-nb btn-blue-nb2">
                Печать
              </button>
            </div>
            <div class="col-xs-3" style="padding-left: 0">
              <button type="button" class="btn btn-primary-nb btn-blue-nb" data-dismiss="modal">Закрыть</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import DateSelector from '../fields/DateSelector.vue';
import SelectPicker from '../fields/SelectPicker.vue';

export default {
  name: 'statistics-tickets-print-modal',
  components: {
    DateSelector,
    SelectPicker,
  },
  props: {
    users: {
      type: Array,
    },
    deps: {
      type: Array,
      required: false,
      default() {
        return [];
      },
    },
  },
  data() {
    return {
      date_type: 'd',
      values: {
        date: '',
        month: '',
        year: '',
      },
      user: '-1',
      dep: '-1',
      fin: '-1',
    };
  },
  watch: {
    bases: {
      immediate: true,
      deep: true,
      handler() {
        if (this.fin === '-1' && this.bases.length > 0 && this.bases[0].fin_sources.length > 0) {
          this.fin = this.bases[0].fin_sources[0].pk;
        }
      },
    },
  },
  computed: {
    bases() {
      return this.$store.getters.bases.filter((b) => !b.hide);
    },
    users_list() {
      const u = [];
      for (const u_row of this.users) {
        u.push({ value: u_row.pk, label: u_row.fio });
      }
      return u;
    },
    deps_list() {
      const u = [];
      for (const u_row of this.deps) {
        u.push({ value: u_row.pk, label: u_row.title });
      }
      return u;
    },
    selected_users() {
      return this.user.split(',');
    },
  },
  methods: {
    change_user(val) {
      let v = val || '';
      if (Array.isArray(v)) {
        v = v.join(',');
      }
      this.user = v;
    },
    change_dep(val) {
      let v = val || '';
      if (Array.isArray(v)) {
        v = v.join(',');
      }
      this.dep = v;
    },
    make_report() {
      // eslint-disable-next-line max-len
      window.open(`/statistic/xls?type=statistics-tickets-print&user=${this.selected_users}&department=${this.dep}&date_type=${this.date_type}&date_values=${encodeURIComponent(JSON.stringify(this.values))}&fin=${this.fin}`, '_blank');
    },
  },
};
</script>
