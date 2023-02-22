<template>
  <tr>
    <td>
      {{ data.label }}
    </td>
    <td>
      <li
        v-for="g in status"
        class="list"
        :key="g.id"
      >
        {{ g }}
      </li>
    </td>
    <td>
      <div class=main-data>
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
          @click=getStatus(data)
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
.form-control.wbr {
  border-right: 1px solid #646d78;
}
.main-data {
    margin: 0px;
  button {
    border-radius: 0;
    width: 125px;
    margin: 0px;
  }
}
.list{
  list-style-type: none;
}
</style>
