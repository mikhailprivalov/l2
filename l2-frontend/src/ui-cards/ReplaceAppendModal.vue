<template>
  <div class="custom-view-wrapper">
    <div class="dg-content">
      Шаблон "{{ messageBody }}".
    </div>
    <div class="dg-content">
      Выберите вариант действий:
    </div>
    <br>

    <button
      class="btn btn-blue-nb"
      @click="handle('replace')"
    >
      Заменить значения
    </button>
    <button
      class="btn btn-blue-nb"
      @click="handle('append')"
    >
      Дописать
    </button>
    <button
      class="btn btn-blue-nb"
      @click="handleDismiss()"
    >
      Отмена
    </button>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import DialogMixin from 'vuejs-dialog/dist/vuejs-dialog-mixin.min';

@Component({
  mixins: [DialogMixin],
})
export default class ReplaceAppendModal extends Vue {
  proceed: any;

  cancel: any;

  messageBody: any;

  handle(platform) {
    this.proceed(platform);
  }

  handleDismiss() {
    this.cancel();
  }
}
</script>

<style scoped>
button {
  width: 100%;
  margin-bottom: 10px;
  float: none;
}
</style>
