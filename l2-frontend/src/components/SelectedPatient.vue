<template>
  <div class="top-root">
    <div class="param"><strong>Пациент:</strong></div>
    <div class="param" v-if="card.pk === -1">
      Не выбран
    </div>
    <div style="display: inline-block" v-else>
      <div class="param">{{card.fio}}</div>
      <div class="param">{{card.sex.toUpperCase()}}</div>
      <div class="param">{{card.age}}</div>
      <div class="param">{{card.bd}}</div>
      <div class="param"><strong v-if="!card.is_rmis">Карта:</strong><strong v-else>РМИС ID:</strong></div>
      <div class="param">{{card.num}}</div>
      <div class="param" v-if="!card.is_rmis">{{card.base}}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SelectedPatient',
  props: {
    card: {
      type: Object,
    },
  },
};
</script>

<style lang="scss" scoped>
  .top-root {
    background: #1f2225;
    padding: 5px;
    color: #fff;
    .param {
      display: inline-block;
      margin-right: 10px;
    }
  }
</style>
