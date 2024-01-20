<template>
  <div
    class="research"
  >
    {{ 'Анализы' }}
    <table class="table">
      <colgroup>
        <col width="30">
        <col width="30">
        <col>
        <col width="30">
        <col width="30">
      </colgroup>
      <tr
        v-for="(research, idx) in props.tube.researches"
        :key="research.pk"
      >
        <td class="border">
          <div class="button">
            <button
              :class="isFirstRow(research.order) ? 'transparent-button-disabled' : 'transparent-button'"
              :disabled="isFirstRow(research.order)"
              @click="updateOrder(idx, research.pk, research.order,'dec_order')"
            >
              <i class="glyphicon glyphicon-arrow-up" />
            </button>
          </div>
        </td>
        <td class="border">
          <div class="button">
            <button
              :class="isLastRow(research.order) ? 'transparent-button-disabled' : 'transparent-button'"
              :disabled="isLastRow(research.order)"
              @click="updateOrder(idx, research.pk, research.order, 'inc_order')"
            >
              <i class="glyphicon glyphicon-arrow-down" />
            </button>
          </div>
        </td>
        <td
          v-tippy
          class="border research-title"
          :title="research.title"
        >
          {{ research.title }}
        </td>
        <td class="border">
          <div class="button">
            <button
              class="transparent-button"
              @click="changeVisibility(research.pk)"
            >
              {{ research.hide ? 'пок' : 'скр' }}
            </button>
          </div>
        </td>
        <td class="border">
          <div class="button">
            <button
              class="transparent-button"
              @click="edit(research.pk)"
            >
              <i class="fa fa-pencil" />
            </button>
          </div>
        </td>
      </tr>
      <tr>
        <td
          colspan="5"
          class="border"
        >
          <div class="button">
            <button
              class="transparent-button"
              @click="addResearch"
            >
              Добавить анализ
            </button>
          </div>
        </td>
      </tr>
    </table>
    <div> {{ props.tube.tubes.length > 0 ? 'Ёмкости' : 'Ёмкости не привязаны' }}</div>
    <div
      v-for="currentTube in props.tube.tubes"
      :key="currentTube.id"
      class="tube-edit"
      @click="editRelation(currentTube.id)"
    >
      <ColorTitled
        :color="currentTube.color"
        :title="currentTube.title"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance } from 'vue';

import ColorTitled from '@/ui-cards/ColorTitled.vue';

const props = defineProps({
  tube: {
    type: Object,
    required: true,
  },
});
const root = getCurrentInstance().proxy.$root;
const emit = defineEmits(['updateOrder', 'changeVisibility', 'edit', 'add', 'editRelationTube']);

const minMaxOrder = computed(() => {
  let min = props.tube.researches[0].order;
  let max = props.tube.researches[0].order;
  for (const row of props.tube.researches) {
    min = Math.min(min, row.order);
    max = Math.max(max, row.order);
  }
  return { min, max };
});

const isFirstRow = (order: number) => order === minMaxOrder.value.min;
const isLastRow = (order: number) => order === minMaxOrder.value.max;

const updateOrder = (researchIdx: number, researchPk: number, researchOrder: number, action: string) => {
  if (action === 'inc_order' && researchOrder < minMaxOrder.value.max) {
    const researchNearbyPk = props.tube.researches[researchIdx + 1].pk;
    emit('updateOrder', { researchPk, researchNearbyPk, action });
  } else if (action === 'dec_order' && researchOrder > minMaxOrder.value.min) {
    const researchNearbyPk = props.tube.researches[researchIdx - 1].pk;
    emit('updateOrder', { researchPk, researchNearbyPk, action });
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

const changeVisibility = (researchPk: number) => {
  emit('changeVisibility', { researchPk });
};

const edit = (researchPk: number) => {
  emit('edit', { researchPk });
};

const addResearch = () => {
  emit('add', { tubes: props.tube.tubes, order: minMaxOrder.value.max + 1 });
};

const editRelation = (relationId) => {
  emit('editRelationTube', { relationId });
};

</script>

<style scoped lang="scss">
.table {
  table-layout: fixed;
}
.border {
  border: 1px solid #bbb;
}
.research {
  background-color: #fff;
  padding: 5px;
  margin: 10px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
}
.research:not(:first-child) {
  margin-top: 0;
}
.research:last-child {
  margin-bottom: 0;
}
.research-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 3px;
  padding-top: 1px;
  padding-bottom: 1px;
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
  border: none;
  padding: 1px 0;
}
.transparent-button:hover {
  background-color: #434a54;
  color: #FFFFFF;
  border: none;
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
  border: none;
  padding: 1px 0;
}

.tube-edit {
  cursor: pointer;
}
.tube-edit:hover {
  background-color: #434a54;
  color: #FFFFFF;
}
.tube-edit:active {
  background-color: #37BC9B;
  color: #FFFFFF;
}
</style>
