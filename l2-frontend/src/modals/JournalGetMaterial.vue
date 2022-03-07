<template>
  <Modal
    show-footer="true"
    white-bg="true"
    max-width="710px"
    width="100%"
    margin-left-right="auto"
    :z-index="1000"
    @close="close"
  >
    <span slot="header">Печать отчёта забора биоматериала</span>
    <div
      slot="body"
      class="popup-body journal"
    >
      <div class="row">
        <div class="col-xs-6">
          <DateSelector
            :date_type.sync="date_type"
            :values.sync="values"
            data-container="body"
          />
        </div>
        <div
          class="col-xs-6"
          style="padding-left: 0"
        >
          <SelectPicker
            :val="user"
            :options="users_list"
            :func="change_user"
            :multiple="users.length > 1"
            :actions_box="users.length > 1"
            data-container="body"
          />
        </div>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-6">
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="close"
          >
            Закрыть
          </button>
        </div>
        <div class="col-xs-6 text-right">
          <button
            class="btn btn-blue-nb"
            type="button"
            @click="make_report"
          >
            Сформировать отчёт
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import Modal from '@/ui-cards/Modal.vue';
import DateSelector from '../fields/DateSelector.vue';
import SelectPicker from '../fields/SelectPicker.vue';

export default {
  name: 'JournalGetMaterial',

  components: { DateSelector, SelectPicker, Modal },
  props: {
    users: {
      type: Array,
    },
  },
  data() {
    return {
      user: '-1',
      date_type: 'd',
      values: {
        date: '',
        month: '',
        year: '',
      },
    };
  },
  computed: {
    users_list() {
      const u = [];
      for (const u_row of this.users) {
        u.push({ value: u_row.pk, label: u_row.fio });
      }
      return u;
    },
    selected_users() {
      return this.user.split(',');
    },
  },
  mounted() {
    window.$('.journal .selectpicker').selectpicker();
  },
  methods: {
    close() {
      this.$emit('close');
    },
    change_user(val) {
      let v = val || '';
      if (Array.isArray(v)) {
        v = v.join(',');
      }
      this.user = v;
    },
    make_report() {
      // eslint-disable-next-line max-len
      window.open(
        `/statistic/xls?type=journal-get-material&users=${encodeURIComponent(JSON.stringify(this.selected_users))}&date_type=${
          this.date_type
        }&values=${encodeURIComponent(JSON.stringify(this.values))}`,
        '_blank',
      );
    },
  },
};
</script>
