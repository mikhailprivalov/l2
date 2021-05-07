<template>
    <modal v-if="agent_to_edit" ref="modalCardfind" @close="hide_modal_agent_edit" show-footer="true" white-bg="true"
             max-width="710px" width="100%" marginLeftRight="auto" margin-top>
        <!-- eslint-disable-next-line max-len -->
        <span slot="header">Редактор – {{agent_type_by_key(agent_to_edit)}} (карта {{card.number}} пациента {{card.family}} {{card.name}} {{card.patronymic}})</span>
        <div slot="body" style="min-height: 140px" class="registry-body">
          <div v-show="!agent_clear">
            <div style="height: 110px">
              <patient-small-picker v-model="agent_card_selected" :base_pk="base_pk"/>
            </div>
            <div class="form-group" v-if="agent_need_doc(agent_to_edit)" style="padding: 10px">
              <label for="ae-f2">Документ-основание:</label>
              <input class="form-control" id="ae-f2" v-model="agent_doc">
            </div>
          </div>
          <div class="checkbox" style="padding-left: 35px;padding-top: 10px" v-if="!!card[agent_to_edit]">
            <label>
              <input type="checkbox" v-model="agent_clear"> очистить представителя
              ({{agent_type_by_key(agent_to_edit)}})
            </label>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div class="col-xs-4">
              <button @click="hide_modal_agent_edit" class="btn btn-primary-nb btn-blue-nb" type="button">
                Отмена
              </button>
            </div>
            <div class="col-xs-4">
              <button :disabled="!valid_agent" @click="save_agent()" class="btn btn-primary-nb btn-blue-nb"
                      type="button">
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </modal>
</template>

<script>
export default {
  name: 'FindPatient',
};
</script>

<style scoped>

</style>
