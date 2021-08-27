<template>
  <Modal @close="close" show-footer="true" white-bg="true" max-width="710px" width="100%" marginLeftRight="auto" :zIndex="1000">
    <span slot="header">Печать отчёта забора биоматериала</span>
    <div slot="body" class="popup-body journal">
      <div class="row">
        <div class="col-xs-6">
          <DateSelector :date_type.sync="date_type" :values.sync="values" dataContainer="body" />
        </div>
        <div class="col-xs-6" style="padding-left: 0">
          <SelectPicker
            :val="user"
            :options="users_list"
            :func="change_user"
            :multiple="users.length > 1"
            :actions_box="users.length > 1"
            dataContainer="body"
          />
        </div>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-6">
          <button @click="close" class="btn btn-blue-nb" type="button">
            Закрыть
          </button>
        </div>
        <div class="col-xs-6 text-right">
          <button @click="make_report" class="btn btn-blue-nb" type="button">
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
  props: {
    users: {
      type: Array,
    },
  },

  components: { DateSelector, SelectPicker, Modal },
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
  mounted() {
    window.$('.journal .selectpicker').selectpicker();
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
