<template>
  <tr>
    <td>
      {{ data.label }}
    </td>
    <td>
      <div class="inner-card">
        <a
          v-tippy="{
            placement: 'right',
            html: '#template-systemctl-' + data.pk,
            arrow: true,
            reactive: true,
            theme: 'light bordered',
            popperOptions: {
              modifiers: {
                preventOverflow: {
                  boundariesElement: 'window',
                },
                hide: {
                  enabled: false,
                },
              },
            },
            interactive: true,
          }"
          href="#"
          class="main-open-link"
          @show="getStatusSystemctl"
        >
          Systemctl
        </a>
      </div>
      <div
        :id="`template-systemctl-${data.pk}`"
      >
        <strong>Systemctl</strong><br>
        <ul
          style="padding-left: 0; list-style-type: none; text-align: left;"
        >
          <li
            v-for="systemctl in systemctl_data"
            :key="systemctl.pk"
          >
            {{ systemctl.status }}
          </li>
        </ul>
      </div>
      <ul style="padding-left: 0; list-style-type: none;">
        <li
          v-for="status in status_list"
          :key="status.pk"
        >
          {{ status.status }}
        </li>
      </ul>
    </td>
    <td>
      <div class="main-data">
        <button
          class="btn btn-blue-nb"
          @click="restartAnalyzer"
        >
          Перезагрузить
        </button>
        <button
          class="btn btn-blue-nb"
          style="position: absolute; width: 135px;"
          @click="getStatus"
        >
          Обновить статус
        </button>
      </div>
    </td>
  </tr>
</template>

<script>
import * as actions from '@/store/action-types';

export default {
  name: 'Row',
  props: {
    data: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      status_list: [],
      systemctl_data: [],
    };
  },
  mounted() {
    if (localStorage.getItem(this.data.pk)) {
      const savedStatus = JSON.parse(localStorage.getItem(this.data.pk));
      if (Array.isArray(savedStatus)) {
        this.status_list = savedStatus;
      }
    }
  },
  methods: {
    async restartAnalyzer() {
      await this.$store.dispatch(actions.INC_LOADING);
      const list = await this.$api('analyzers/restart-analyzer', this.data, 'pk');
      this.status_list = list.data;
      await this.$store.dispatch(actions.DEC_LOADING);
      localStorage.setItem(this.data.pk, JSON.stringify(this.status_list));
    },
    async getStatus() {
      await this.$store.dispatch(actions.INC_LOADING);
      const list = await this.$api('analyzers/status-analyzer', this.data, 'pk');
      this.status_list = list.data;
      await this.$store.dispatch(actions.DEC_LOADING);
      localStorage.setItem(this.data.pk, JSON.stringify(this.status_list));
    },
    async getStatusSystemctl() {
      const list = await this.$api('analyzers/status-systemctl', this.data, 'pk');
      this.systemctl_data = list.data;
    },
  },
};
</script>

<style lang="scss" scoped>
.inner {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}
.main-open-link {
  margin-left: 3px;
  font-size: 16px;
}
.main-data {
  margin: 0;
  button {
    border-radius: 0;
    width: 125px;
    margin: 0;
  }
}
</style>
