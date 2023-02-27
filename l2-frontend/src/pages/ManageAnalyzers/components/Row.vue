<template>
  <tr>
    <td>
      {{ data.label }}
    </td>
    <td>
      <ul style="padding-left: 0; list-style-type: none;">
        <li
          v-for="g in status"
          :key="g.id"
        >
          {{ g }}
        </li>
      </ul>
    </td>
    <td>
      <div class="main-data">
        <button
          v-tippy
          class="btn btn-blue-nb"
          :value="data"
          @click="restartAnalyze(data)"
        >
          Перезагрузить
        </button>
        <button
          v-tippy
          class="btn btn-blue-nb"
          :value="data"
          style="position: absolute;"
          @click="getStatus(data)"
        >
          Cтатус
        </button>
      </div>
    </td>
  </tr>
</template>

<script>
import * as actions from '../../../store/action-types';

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
      status: [],
    };
  },
  mounted() {
    if (localStorage.getItem(this.data.pk)) {
      const savedStatus = JSON.parse(localStorage.getItem(this.data.pk));
      if (Array.isArray(savedStatus)) {
        this.status = savedStatus;
      }
    }
  },
  methods: {
    async restartAnalyze(data) {
      await this.$store.dispatch(actions.INC_LOADING);
      const list = await this.$api('restart-analyze', {
        pk: data.pk,
      });
      this.status = list.data;
      await this.$store.dispatch(actions.DEC_LOADING);
      localStorage.setItem(data.pk, JSON.stringify(this.status));
    },
    async getStatus(data) {
      await this.$store.dispatch(actions.INC_LOADING);
      const list = await this.$api('status-analyzer', {
        pk: data.pk,
      });
      this.status = list.data;
      await this.$store.dispatch(actions.DEC_LOADING);
      localStorage.setItem(data.pk, JSON.stringify(this.status));
    },
  },
};
</script>

<style lang="scss" scoped>
.main-data {
    margin: 0;
  button {
    border-radius: 0;
    width: 125px;
    margin: 0;
  }
}
</style>
