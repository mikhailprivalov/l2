<template>
  <modal
    v-if="agent_to_edit"
    ref="modalCardfind"
    show-footer="true"
    white-bg="true"
    max-width="710px"
    width="100%"
    margin-left-right="auto"
    margin-top
    @close="hide_modal_agent_edit"
  >
    <!-- eslint-disable-next-line max-len -->
    <span slot="header">Редактор – {{ agent_type_by_key(agent_to_edit) }} (карта {{ card.number }} пациента {{ card.family }} {{ card.name }} {{ card.patronymic }})</span>
    <div
      slot="body"
      style="min-height: 140px"
      class="registry-body"
    >
      <div v-show="!agent_clear">
        <div style="height: 110px">
          <patient-small-picker
            v-model="agent_card_selected"
            :base_pk="base_pk"
          />
        </div>
        <div
          v-if="agent_need_doc(agent_to_edit)"
          class="form-group"
          style="padding: 10px"
        >
          <label for="ae-f2">Документ-основание:</label>
          <input
            id="ae-f2"
            v-model="agent_doc"
            class="form-control"
          >
        </div>
      </div>
      <div
        v-if="!!card[agent_to_edit]"
        class="checkbox"
        style="padding-left: 35px;padding-top: 10px"
      >
        <label>
          <input
            v-model="agent_clear"
            type="checkbox"
          > очистить представителя
          ({{ agent_type_by_key(agent_to_edit) }})
        </label>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="hide_modal_agent_edit"
          >
            Отмена
          </button>
        </div>
        <div class="col-xs-4">
          <button
            :disabled="!valid_agent"
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="save_agent()"
          >
            Сохранить
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script lang="ts">
export default {
  name: 'FindPatient',
};
</script>

<style scoped>

</style>
