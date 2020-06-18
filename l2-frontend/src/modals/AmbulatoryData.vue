<template>
  <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="680px" width="100%"
         marginLeftRight="auto" margin-top>
      <span slot="header">Изменить родителя</span>
    <div slot="body" style="min-height: 340px">
      <h6><strong>Пациент: </strong>{{patientFio}}</h6>
      <div class="row" id="row-box">
        <div class="col-xs-6">
          <h6><strong>Изменить принадлежность:</strong></h6>
        </div>
        <div class="col-xs-6" id="box-right">
          <h6><strong>Главное направление:</strong></h6>
        </div>
      </div>
    </div>

    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button type="button"class="btn btn-primary-nb btn-blue-nb">
            Сохранить
          </button>
        </div>
        <div class="col-xs-4">
          <button type="button" @click="hide_modal" class="btn btn-primary-nb btn-blue-nb">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </modal>

</template>

<script>
    export default {
        name: "AmbulatoryData",
      methods: {
          hide_modal() {
        // if (this.$refs.modal) {
        //   this.$refs.modal.$el.style.display = 'none'
        // }
        this.$root.$emit('ambulatory_data')
      }
      }
    }
</script>

<style scoped>

</style>
