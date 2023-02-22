<template>
  <div>
    <h5>
      Анализаторы <i
        class="name table"
      />
    </h5>
    <table class="table table-bordered table-responsive table-condensed">
      <colgroup>
        <col width="125">
        <col width="300">
        <col width="80">
      </colgroup>
      <thead>
        <tr>
          <th>Название анализатора</th>
          <th>Статус анализатора</th>
          <th>Действие</th>
        </tr>
      </thead>
      <tbody>
        <Row v-for="row in analyzers"
             :key="row.pk"
             :value="row.pk"
             :data="row"
        />
        <tr v-if="analyzers.length === 0">
          <td colspan="3">
            Нет Анализаторов
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
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
      const rows = await this.$api('manage-profile-analyzer');
      this.analyzers = rows.data;
    },
  },
};
</script>

<style lang="scss" scoped>
</style>
