<template>
  <div>
    <h5>
      Анализаторы
    </h5>
    <table class="table table-fixed table-bordered table-responsive table-condensed">
      <colgroup>
        <col style="width: 20%;">
        <col style="width: 55%;">
        <col style="width: 25%;">
      </colgroup>
      <thead>
        <tr>
          <th>Название анализатора</th>
          <th>Статус анализатора</th>
          <th>Действие</th>
        </tr>
      </thead>
      <tbody>
        <Row
          v-for="row in analyzers"
          :key="row.pk"
          :data="row"
        />
        <tr v-if="analyzers.length === 0">
          <td colspan="3">
            Нет анализаторов
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import * as actions from '@/store/action-types';

import Row from './components/Row.vue';

export default {
  name: 'ManageAnalyzers',
  components: {
    Row,
  },
  data() {
    return {
      analyzers: [],
    };
  },
  mounted() {
    this.getProfileAnalyzer();
  },
  methods: {
    async getProfileAnalyzer() {
      await this.$store.dispatch(actions.INC_LOADING);
      const rows = await this.$api('analyzers/manage-profile-analyzer');
      this.analyzers = rows.data;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>
