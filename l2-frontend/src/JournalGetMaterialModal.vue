<template>
  <div class="modal fade" tabindex="-1">
    <div class="modal-dialog" style="width: 40%;min-width: 680px">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button>
          <h4 class="modal-title">Печать отчёта забора биоматериала</h4>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-xs-6">
              <date-selector></date-selector>
            </div>
            <div class="col-xs-6" style="padding-left: 0">
              <select-picker :val="user" :options="users_list" :func="change_user" :multiple="users.length > 1" :actions_box="users.length > 1"></select-picker>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <div class="row">
            <div class="col-xs-3"></div>
            <div class="col-xs-6">
              <button type="button" class="btn btn-primary-nb btn-blue-nb2">Сформировать отчёт</button>
            </div>
            <div class="col-xs-3" style="padding-left: 0">
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
  import SelectPicker from './SelectPicker.vue'

  export default {
    name: 'journal-get-material-modal',
    props: {
      users: {
        type: Array
      }
    },
    data() {
      return {
        user: '-1'
      }
    },
    computed:{
      users_list(){
        let u = []
        for(let u_row of this.users){
          u.push({value: u_row.pk, label: u_row.fio})
        }
        return u
      }
    },
    methods: {
      change_user(v) {
        if(!v){
          v = ""
        }
        if(Array.isArray(obj)){
          v.join(",")
        }
        this.user = v
      }
    },
    components: {DateSelector, SelectPicker}
  }
</script>
