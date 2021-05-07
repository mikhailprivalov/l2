<template>
  <div>
    <label>
      Модель:
      <select v-model="model">
        <option v-for="m in models" :key="m">{{m}}</option>
      </select>
    </label>
    <div>
      Отправить в задание на синхронизацию: с <input v-model.number="from" type="number" min="0"
                                                     :disabled="model === '' || insend"/>
      по <input v-model.number="to" :disabled="model === '' || insend" type="number" min="0"/>
      <button :disabled="model === '' || insend" @click="do_send">&rAarr;</button>
    </div>
    <div v-if="insend || oksend">
      <progress :max="Math.max(to-from + 1, 1)" :value="csended + 1" style="width: 100%;"></progress>
      <div class="text-center">
        Отправка {{csended + 1}}/{{Math.max(to-from + 1, 1)}} ({{Math.round((csended + 1)/(Math.max(to-from + 1, 1))*100)}}%)
      </div>
      <div class="text-center">Исполнение задания можно проверить в RabbitMQ Management или в приложении-интеграторе
      </div>
    </div>
  </div>
</template>

<script>
import * as actions from '../store/action-types';

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
        'directory.RMISOrgs',
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
      oksend: false,
    };
  },
  watch: {
    model() {
      this.loadModelCountMax();
    },
  },
  methods: {
    loadModelCountMax() {
      if (this.model === '') return;
      this.from = 0;
      this.to = 0;
      this.csended = 0;
      this.oksend = false;
      this.$store.dispatch(actions.INC_LOADING);
      window.$.ajax({ url: '/mainmenu/rmq/count', data: { model: this.model } }).done((data) => {
        this.to = data.count;
      }).always(() => {
        this.$store.dispatch(actions.DEC_LOADING);
      });
    },
    do_send() {
      if (this.model === '' || this.insend) return;
      this.insend = true;
      this.oksend = false;
      this.csended = 0;
      this.send();
    },
    send() {
      window.$.ajax({ url: '/mainmenu/rmq/send', data: { model: this.model, pk: this.csended + this.from } }).always(() => {
        if (this.csended + this.from >= this.to) {
          this.insend = false;
          this.oksend = true;
        } else {
          this.csended++;
          this.send();
        }
      });
    },
  },
};
</script>

<style scoped>

</style>
