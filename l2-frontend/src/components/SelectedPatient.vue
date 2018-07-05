<template>
  <div class="top-root">
    <div class="param"><strong>Выбранный пациент:</strong></div>
    <div class="param">{{patient.fio}}</div>
    <div class="param">{{patient.sex}}</div>
    <div class="param">{{patient.age}}</div>
    <div class="param">{{patient.bd}}</div>
  </div>
</template>

<script>
  export default {
    name: 'SelectedPatient',
    data() {
      return {
        patient: {
          fio: 'Иванов Иван Иванович',
          sex: 'М',
          bd: '24.01.1997',
          age: '21 год',
        },
        card: {
          category: 'Поликлиника',
          num: '22293',
        }
      }
    }
  }
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
