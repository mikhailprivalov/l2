<template>
  <div class="fill-template">
    <div class="flex">
      <button
        class="btn btn-blue-nb row-item"
        @click="fill"
      >
        Заполнить по шаблону
      </button>
      <button
        class="btn btn-blue-nb row-item"
        @click="clear"
      >
        Очистить шаблон
      </button>
    </div>
    <div class="flex">
      <button
        class="btn btn-blue-nb row-item"
        @click="fillByEmployeesTemplate"
      >
        По умолчанию
      </button>
      <button
        class="btn btn-blue-nb row-item"
      >
        Из предыдущего
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">

import { getCurrentInstance } from 'vue';

const emit = defineEmits(['fill', 'clear']);
const root = getCurrentInstance().proxy.$root;

const fill = () => {
  emit('fill');
};
const clear = () => {
  emit('clear');
};

const fillByEmployeesTemplate = async () => {
  try {
    await root.$dialog.confirm('Выберите вариант заполнения', {
      okText: 'Дописать',
      cancelText: 'Заменить',
    });
    console.log('выбрано дописать');
  } catch (_) {
    console.log('выбрано заменить');
  }
};
</script>

<style scoped lang="scss">
.flex {
  display: flex;
  gap: 5px;
  margin: 2px;
}
.row-item {
  flex: 1;
}
.fill-template {
  white-space: normal;
}
</style>
