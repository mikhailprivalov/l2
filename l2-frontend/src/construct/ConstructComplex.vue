<template>
  <div>
    <Treeselect
    placeholder="Выберите комплекс"/>
    <div class="block shadow">
      <h4>Редактирование комплекса</h4>
    </div>
    <div class="block shadow">
      <h4>Список услуг в комплексе</h4>
    </div>
    <div class="block shadow">
      <h4>Добавление услуги в комплекс</h4>
    </div>
  </div>
</template>

<script setup lang="ts">
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

</script>

<style scoped lang="scss">
.shadow {
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
}
.block {
  background-color: #fff;
  border-radius: 5px;
  margin-bottom: 20px;
}
</style>
