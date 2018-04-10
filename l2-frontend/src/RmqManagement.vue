<template>
  <div>
    <label>
      Модель:
      <select v-model="model">
        <option v-for="m in models">{{m}}</option>
      </select>
    </label>
    <div>
      Отправить в задание на синхронизацию: с <input v-model.number="from" type="number" min="0"
                                                     :disabled="model === '' || insend"/>
      по <input v-model.number="to" :disabled="model === '' || insend" type="number" min="0"/>
      <button :disabled="model === '' || insend" @click="do_send">&rAarr;</button>
    </div>
    <div v-if="insend || oksend">
      <progress :max="Math.max(to-from, 1)" :value="csended" style="width: 100%;"></progress>
      <div class="text-center">Отправка {{csended}}/{{Math.max(to-from, 1)}} ({{Math.round(csended/(Math.max(to-from,
        1))*100)}}%)
      </div>
      <div class="text-center">Исполнение задания можно проверить в RabbitMQ Management или в приложении-интеграторе
      </div>
    </div>
  </div>
</template>

<script>
  import * as action_types from './store/action-types'

  export default {
    name: 'rmq-management',
    data() {
      return {
        messages: null,
        models: [
          'clients.CardBase',
          'clients.Individual',
          'clients.Card',
          'directions.IstochnikiFinansirovaniya',
          'podrazdeleniya.Podrazdeleniya',
          'users.DoctorProfile',
          'researches.Tubes',
          'directory.Researches',
          'directory.Fractions',
          'directory.ParaclinicInputGroups',
          'directory.ParaclinicInputField',
          'directions.Napravleniya',
          'directions.Issledovaniya',
          'directions.TubesRegistration',
          'directions.Result',
          'directions.ParaclinicResult',
        ],
        model: '',
        from: 0,
        to: 0,
        csended: 0,
        insend: false,
        oksend: false
      }
    },
    watch: {
      model() {
        this.loadModelCountMax()
      }
    },
    methods: {
      loadModelCountMax() {
        if (this.model === '')
          return
        let vm = this
        vm.from = 0
        vm.to = 0
        vm.csended = 0
        vm.oksend = false
        vm.$store.dispatch(action_types.INC_LOADING).then()
        $.ajax({url: '/mainmenu/rmq/count', data: {model: vm.model}}).done(data => {
          vm.to = data.count
        }).always(() => {
          vm.$store.dispatch(action_types.DEC_LOADING).then()
        })
      },
      do_send() {
        if (this.model === '' || this.insend)
          return
        let vm = this
        vm.insend = true
        vm.oksend = false
        vm.csended = 0
        vm.send()
      },
      send() {
        let vm = this
        $.ajax({url: '/mainmenu/rmq/send', data: {model: vm.model, pk: vm.csended + vm.from}}).always(() => {
          vm.csended++
          if (vm.csended + vm.from >= vm.to) {
            vm.insend = false
            vm.oksend = true
          } else {
            vm.send()
          }
        })
      }
    }
  }
</script>

<style scoped>

</style>
