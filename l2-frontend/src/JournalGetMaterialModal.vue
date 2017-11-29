<template>
  <div class="modal fade" tabindex="-1">
    <div class="modal-dialog" style="width: 50%;">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
          <h4 class="modal-title">Печать отчёта забора биоматериала</h4>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-xs-4" style="padding-right: 3px;">
              <select class="selectpicker" data-width="100%" v-model="type">
                <option value="d">За день</option>
                <option value="m">За месяц</option>
              </select>
            </div>
            <div class="col-xs-8">
              <div v-if="type == 'd'">
                <input type="text" class="form-control no-context" name="dateday-type"/>
              </div>
              <div class="row" v-if="type == 'm'">
                <div class="col-xs-6" style="padding-right: 3px;">
                  <select class="selectpicker" data-width="100%">
                    <option value="0">Январь</option>
                    <option value="1">Февраль</option>
                    <option value="2">Март</option>
                    <option value="3">Апрель</option>
                    <option value="4">Май</option>
                    <option value="5">Июнь</option>
                    <option value="6">Июль</option>
                    <option value="7">Август</option>
                    <option value="8">Сентябрь</option>
                    <option value="9">Октябрь</option>
                    <option value="10">Ноябрь</option>
                    <option value="11">Декабрь</option>
                  </select>
                </div>
                <div class="col-xs-6">
                  <input type="number" class="form-control year" id="m-year" value="" min="2015" max="2100"/>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <div class="row">
            <div class="col-xs-9"></div>
            <div class="col-xs-3">
              <button type="button" class="btn btn-primary-nb btn-blue-nb" data-dismiss="modal">Закрыть</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'journal-get-material-modal',
    data() {
      return {
        type: 'd'
      }
    },
    methods: {}
  }
</script>
