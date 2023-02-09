<template>
  <div>
    <h5>
      Анализаторы<i
        class="name table"
      />
    </h5>
    <table class="table table-bordered table-responsive table-condensed">
      <colgroup>
        <col width="300">
        <col width="200">
        <col>
      </colgroup>
      <thead>
        <tr>
          <th>Название анализатора</th>
          <th>Действие</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="r in getAnalyzer"
          :key="r.id"
        >
          <td>
            {{ r.title }}
          </td>
          <td>
            <input
              type="button"
              class="btn btn-primary-nb form-control"
              value="Перезагрузить"
              style="margin-top: 15px"
              @click="restartAnalyze"
            >
          </td>
        </tr>
        <tr v-if="getAnalyzer.length === 0">
          <td colspan="6">
            Нет Анализаторов
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script lang="ts">

export default {
  name: 'ManageAnalyze',
  data() {
    return {
      analyzer: {},
      count: 0,
    };
  },
  methods: {
    async getAnalyzer() {
      this.analyzer = await this.$api('manage-analyze');
    },
    restartAnalyze() {
      this.count += 1;
    },
  },
};
</script>

<style lang="scss" scoped>

.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
</style>
