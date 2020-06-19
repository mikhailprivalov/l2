<template>
    <modal ref="modal" @close="hide_modal" show-footer="true" white-bg="true" max-width="680px" width="100%"
         marginLeftRight="auto" margin-top>
    <span slot="header">Вакцинация пациента
    </span>
    <div slot="body" style="min-height: 200px" class="registry-body">
      <table class="table table-bordered table-condensed table-sm-pd"
             style="table-layout: fixed; font-size: 12px">
        <colgroup>
          <col width="70" />
          <col/>
          <col/>
          <col/>
          <col/>
          <col/>
          <col/>
          <col width="45" />
        </colgroup>
        <thead>
        <tr>
          <th>Дата</th>
          <th>Название</th>
          <th>Серия</th>
          <th>Доза</th>
          <th>Способ</th>
          <th>Этап</th>
          <th>Отвод</th>
          <th></th>
        </tr>
        </thead>
        <tbody>
        </tbody>
      </table>
      <div style="margin: 0 auto; width: 200px">
        <button class="btn btn-primary-nb btn-blue-nb"
                type="button"><i class="fa fa-plus"></i> Создать запись</button>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-10">
        </div>
        <div class="col-xs-2">
          <button @click="hide_modal" class="btn btn-primary-nb btn-blue-nb" type="button">
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
