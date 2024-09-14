<template>
  <div class="row">
    <div class="col-xs-1" />
    <div class="col-xs-10">
      <div class="list-group">
        <button
          type="button"
          class="list-group-item"
          @click="clearLogs"
        >
          <span class="badge">устар. {{ logsToDelete }} из {{ totalLogs }}</span>
          Очистить записи в логах, которые старше {{ logsStoreDays | pluralDays }}
        </button>
        <button
          type="button"
          class="list-group-item"
          @click="clearArchivedCards"
        >
          <span class="badge">{{ totalArchivedCards }}</span>
          Очистить архивные карты без направлений
        </button>
        <button
          type="button"
          class="list-group-item"
          @click="clearIndividualsWithoutCards"
        >
          <span class="badge">{{ totalIndividualsWithoutCards }}</span>
          Очистить пациентов без карт
        </button>
        <button
          type="button"
          class="list-group-item"
        >
          <ul class="nav navbar-nav">
            <LoadFile
              :is-write-patient-ecp="true"
              :title-button="titleButton"
            />
          </ul>
          <ul class="nav navbar-nav">
            <LoadFile
              :is-load-result-service="true"
              :title-button="loadResultService"
            />
          </ul>
          <ui class="nav navbar-nav">
            <UploadFileModal
              tag="li"
              :forms-file="['100.02']"
            />
          </ui>
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import * as actions from '@/store/action-types';
import LoadFile from '@/ui-cards/LoadFile.vue';
import UploadFileModal from '@/modals/UploadFileModal.vue';

export default {
  name: 'Utils',
  components: { UploadFileModal, LoadFile },
  data() {
    return {
      totalLogs: 0,
      logsToDelete: 0,
      logsStoreDays: 0,
      totalArchivedCards: 0,
      totalIndividualsWithoutCards: 0,
      titleButton: 'для записи в ЕЦП',
      loadResultService: 'загрузить результаты услуг',
    };
  },
  async mounted() {
    await Promise.all([
      this.loadLogsStats(),
      this.loadArchivedCardsStats(),
      this.loadIndividualsWithoutCardsStats(),
    ]);
  },
  methods: {
    async loadLogsStats() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { total, storeDays, toDelete } = await this.$api('health/log/stats');
      this.totalLogs = total;
      this.logsToDelete = toDelete;
      this.logsStoreDays = storeDays;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async loadArchivedCardsStats() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { total } = await this.$api('health/archive-cards/stats');
      this.totalArchivedCards = total;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async loadIndividualsWithoutCardsStats() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { total } = await this.$api('health/patients/stats');
      this.totalIndividualsWithoutCards = total;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async clearLogs() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { deleted } = await this.$api('health/log/cleanup');
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('msg', 'ok', `Удалено записей: ${deleted}`);
      await this.loadLogsStats();
    },
    async clearArchivedCards() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { deleted } = await this.$api('health/archive-cards/cleanup');
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('msg', 'ok', `Удалено карт: ${deleted}`);
      await this.loadArchivedCardsStats();
    },
    async clearIndividualsWithoutCards() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { deleted } = await this.$api('health/patients/cleanup');
      await this.$store.dispatch(actions.DEC_LOADING);
      this.$root.$emit('msg', 'ok', `Удалено пациентов: ${deleted}`);
      await this.loadIndividualsWithoutCardsStats();
    },
  },
};
</script>
