<template>
  <div class="top-root">
    <div class="param">
      <strong>Пациент:</strong>
    </div>
    <div
      v-if="card.pk === -1"
      class="param"
    >
      Не выбран
    </div>
    <div
      v-else
      style="display: inline-block"
    >
      <div class="param">
        {{ props.card.fio }}
      </div>
      <div class="param">
        {{ props.card.sex.toUpperCase() }}
      </div>
      <div class="param">
        {{ props.card.age }}
      </div>
      <div class="param">
        {{ props.card.bd }}
      </div>
      <div class="param">
        <strong v-if="!props.card.is_rmis">Карта:</strong><strong v-else>РМИС ID:</strong>
      </div>
      <div class="param">
        {{ props.card.num }}
      </div>
      <div
        v-if="!props.card.is_rmis"
        class="param"
      >
        {{ props.card.base }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PropType } from 'vue';

interface Card {
  pk: number;
  fio: string;
  sex: string;
  age: string | number;
  bd: string;
  is_rmis: boolean;
  num: string | number;
  base?: string;
}

const props = defineProps({
  card: {
    type: Object as PropType<Card>,
    required: true,
  },
});
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
