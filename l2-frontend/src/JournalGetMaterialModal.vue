<template>
  <div class="modal fade" tabindex="-1">
    <div class="modal-dialog" style="width: 50%;">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
          <h4 class="modal-title">Печать отчёта забора биоматериала</h4>
        </div>
        <div class="modal-body">
          <date-selector></date-selector>
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
  import DateSelector from './DateSelector.vue'

  export default {
    name: 'journal-get-material-modal',
    data() {
      return {}
    },
    methods: {},
    components: { DateSelector }
  }
</script>
