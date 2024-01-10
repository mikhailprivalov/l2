<template>
  <div class="tube-group">
    <ColorTitled
      :title="props.tube.title"
      :color="props.tube.color"
    />
    <table class="table">
      <colgroup>
        <col style="width: 60px">
        <col style="min-width: 100px">
        <col style="min-width: 70px">
        <col style="min-width: 70px">
        <col style="min-width: 70px">
        <col style="width: 30px">
      </colgroup>
      <thead>
        <tr>
          <th />
          <th><strong>Фракция</strong></th>
          <th><strong>По умолчанию</strong></th>
          <th><strong>Варианты</strong></th>
          <th><strong>Ед. изм</strong></th>
        </tr>
      </thead>
      <tr
        v-for="(fraction, idx) in props.tube.fractions"
        :key="fraction.pk"
      >
        <td>
          <div class="button">
            <button
              :class="isFirstRow(fraction.order) ? 'transparent-button-disabled' : 'transparent-button'"
              :disabled="isFirstRow(fraction.order)"
              @click="updateOrder(idx, fraction.pk, fraction.order, 'dec_order')"
            >
              <i class="glyphicon glyphicon-arrow-up" />
            </button>
            <button
              :class="isLastRow(fraction.order) ? 'transparent-button-disabled' : 'transparent-button'"
              :disabled="isLastRow(fraction.order)"
              @click="updateOrder(idx, fraction.pk, fraction.order, 'inc_order')"
            >
              <i class="glyphicon glyphicon-arrow-down" />
            </button>
          </div>
        </td>
        <td class="padding-td">
          <input
            v-model="fraction.title"
            class="form-control fraction-input"
            placeholder="Введите название фракции"
          >
        </td>
        <td class="padding-td">
          <input
            class="form-control fraction-input"
            placeholder="Введите значение"
          >
        </td>
        <td class="padding-td">
          <input
            v-model="fraction.variants"
            class="form-control fraction-input"
          >
        </td>
        <td class="padding-td">
          <input
            v-model="fraction.unit"
            class="form-control fraction-input"
            placeholder="Введите ед. изм."
          >
        </td>
        <td class="padding-td">
          <input
            class="form-control fraction-input"
            placeholder="Введите ед. изм."
            @click="edit(fraction.pk)"
          >
        </td>
      </tr>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, PropType } from 'vue';

import ColorTitled from '@/ui-cards/ColorTitled.vue';
import { tubeData } from '@/construct/ResearchDetail.vue';

const root = getCurrentInstance().proxy.$root;

const props = defineProps({
  tube: {
    type: Object as PropType<tubeData>,
    required: true,
  },
});
const emit = defineEmits(['updateOrder', 'edit']);

const minMaxOrder = computed(() => {
  const { fractions } = props.tube;
  let min = 0;
  let max = 0;
  for (const fraction of fractions) {
    if (min === 0) {
      min = fraction.order;
    } else {
      min = Math.min(min, fraction.order);
    }
    max = Math.max(max, fraction.order);
  }
  return { min, max };
});

const isFirstRow = (order: number) => order === minMaxOrder.value.min;
const isLastRow = (order: number) => order === minMaxOrder.value.max;

const updateOrder = (fractionIdx: number, fractionPk: number, fractionOrder: number, action: string) => {
  if (action === 'inc_order' && fractionOrder < minMaxOrder.value.max) {
    const fractionNearbyPk = props.tube.fractions[fractionIdx + 1].pk;
    emit('updateOrder', { fractionPk, fractionNearbyPk, action });
  } else if (action === 'dec_order' && fractionOrder > minMaxOrder.value.min) {
    const fractionNearbyPk = props.tube.fractions[fractionIdx - 1].pk;
    emit('updateOrder', { fractionPk, fractionNearbyPk, action });
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

const edit = (fractionPk: number) => {
  emit('edit', { fractionPk });
};

</script>

<style scoped lang="scss">
.tube-group {
  margin-bottom: 10px;
  background-color: #fff;
  padding: 10px 5px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
  overflow-y: auto;
}
.table {
  table-layout: fixed;
  margin-bottom: 0;
}
.padding-td {
  padding: 2px 3px;
}
.no-left-padding {
  padding-left: 0;
}
.no-right-padding {
  padding-right: 0;
}
.border {
  border: 1px solid #bbb;
}
.fraction-input {
  height: 28px;
}

.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
.transparent-button {
  background-color: transparent;
  align-self: stretch;
  flex: 1;
  color: #434A54;
  border: 1px solid #AAB2BD;
  border-radius: 4px;
  padding: 3px 2px;
  margin: 0px 1px;
}
.transparent-button:hover {
  background-color: #434a54;
  color: #FFFFFF;
}
.transparent-button:active {
  background-color: #37BC9B;
  color: #FFFFFF;
}
.transparent-button-disabled {
  color: #abaeb3;
  cursor: not-allowed;
  background-color: transparent;
  align-self: stretch;
  flex: 1;
  border: 1px solid #AAB2BD;
  border-radius: 4px;
  padding: 3px 2px;
  margin: 0 1px;
}
</style>
