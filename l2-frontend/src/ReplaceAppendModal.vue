<template>
  <div class="custom-view-wrapper">
    <div class="dg-content">Шаблон "{{messageBody}}".</div>
    <div class="dg-content">Выберите вариант действий:</div><br/>

    <button :options="options" @click="handle('replace')" class="btn btn-blue-nb">Заменить значения</button>
    <button :options="options" @click="handle('append')" class="btn btn-blue-nb">Дописать</button>
    <button :options="options" @click="handleDismiss()" class="btn btn-blue-nb">Отмена</button>
  </div>
</template>

<script>
  import DialogMixin from 'vuejs-dialog/dist/vuejs-dialog-mixin.min'

  export default {
    mixins: [DialogMixin],
    methods: {
      handle(platform) {
        this.proceed(platform)
      },
      handleDismiss() {
        this.cancel()
      }
    },
  }
</script>

<style scoped>
  button {
    width: 100%;
    margin-bottom: 10px;
    float: none;
  }
</style>
