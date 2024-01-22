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
        <col style="width: 170px">
        <col style="width: 120px">
        <col style="min-width: 70px">
        <col style="width: 30px">
      </colgroup>
      <thead>
        <tr>
          <th />
          <th><strong>Фракция</strong></th>
          <th><strong>Ед. изм</strong></th>
          <th><strong>Код ЕЦП</strong></th>
          <th><strong>ФСЛИ</strong></th>
          <th />
        </tr>
      </thead>
      <tr
        v-for="(fraction, idx) in sortedFractions"
        :key="fraction.pk"
      >
        <td>
          <div class="button">
            <button
              :class="isFirstRow(fraction.order) ? 'transparent-button-disabled' : 'transparent-button'"
              :disabled="isFirstRow(fraction.order)"
              @click="updateOrder(idx, fraction.order, 'dec_order')"
            >
              <i class="glyphicon glyphicon-arrow-up" />
            </button>
            <button
              :class="isLastRow(fraction.order) ? 'transparent-button-disabled' : 'transparent-button'"
              :disabled="isLastRow(fraction.order)"
              @click="updateOrder(idx, fraction.order, 'inc_order')"
            >
              <i class="glyphicon glyphicon-arrow-down" />
            </button>
          </div>
        </td>
        <td class="padding-td">
          <input
            v-model="fraction.title"
            v-tippy="{
              maxWidth: '50%',
            }"
            :title="fraction.title"
            class="form-control fraction-input"
            placeholder="Введите название"
          >
        </td>
        <td class="padding-td">
          <UnitTreeselect
            :option="props.units"
            :select="fraction.unitId"
          />
        </td>
        <td class="padding-td">
          <input
            v-model="fraction.ecpId"
            class="form-control fraction-input"
            placeholder="Введите код"
          >
        </td>
        <td class="padding-td">
          <Treeselect
            v-model="fraction.fsli"
            :async="true"
            :load-options="getFsli"
            class="treeselect-28px"
            :append-to-body="true"
            loading-text="Загрузка"
            no-results-text="Не найдено"
            search-prompt-text="Начните писать для поиска"
            :cache-options="false"
          >
            <div
              slot="value-label"
              slot-scope="{ node }"
            >
              {{ node.raw.id || fraction.fsli }}
            </div>
            <label
              slot="option-label"
              slot-scope="{ node }"
              v-tippy="{
                maxWidth: '50%'
              }"
              :title="node.label"
              class="fsli-options"
            > {{ node.label }}</label>
          </Treeselect>
        </td>
        <td>
          <div class="button">
            <button
              class="transparent-button"
              @click="edit(fraction.order)"
            >
              <i class="fa fa-pencil" />
            </button>
          </div>
        </td>
      </tr>
    </table>
    <div class="flex-right">
      <div class="add-button">
        <button
          class="transparent-button"
          @click="addFraction"
        >
          <i class="fa fa-plus" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance, PropType,
} from 'vue';
import Treeselect, { ASYNC_SEARCH } from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import ColorTitled from '@/ui-cards/ColorTitled.vue';
import { tubeData } from '@/construct/ResearchDetail.vue';
import api from '@/api';
import UnitTreeselect from '@/construct/unitTreeselect.vue';

const root = getCurrentInstance().proxy.$root;

const props = defineProps({
  tube: {
    type: Object as PropType<tubeData>,
    required: true,
  },
  tubeidx: {
    type: Number,
    required: true,
  },
  units: {
    type: Array,
    required: true,
  },
});
const emit = defineEmits(['updateOrder', 'edit', 'addFraction']);

const sortedFractions = computed(() => {
  const res = [...props.tube.fractions];
  const result = res.sort((x, y) => x.order - y.order);
  return result;
});

const minMaxOrder = computed(() => {
  let min = sortedFractions.value[0].order;
  let max = sortedFractions.value[0].order;
  for (const fraction of sortedFractions.value) {
    min = Math.min(min, fraction.order);
    max = Math.max(max, fraction.order);
  }
  return { min, max };
});

const isFirstRow = (order: number) => order === minMaxOrder.value.min;
const isLastRow = (order: number) => order === minMaxOrder.value.max;

const updateOrder = (fractionIdx: number, fractionOrder: number, action: string) => {
  if (action === 'inc_order' && fractionOrder < minMaxOrder.value.max) {
    const fractionNearbyOrder = sortedFractions.value[fractionIdx + 1].order;
    emit('updateOrder', {
      tubeIdx: props.tubeidx, fractionNearbyOrder, fractionOrder, action,
    });
  } else if (action === 'dec_order' && fractionOrder > minMaxOrder.value.min) {
    const fractionNearbyOrder = sortedFractions.value[fractionIdx - 1].order;
    emit('updateOrder', {
      tubeIdx: props.tubeidx, fractionNearbyOrder, fractionOrder, action,
    });
  } else {
    root.$emit('msg', 'error', 'Ошибка');
  }
};

const edit = (fractionOrder: number) => {
  emit('edit', { fractionOrder, tubeIdx: props.tubeidx });
};

const getFsli = async ({ action, searchQuery, callback }) => {
  if (action === ASYNC_SEARCH) {
    const { data } = await api(`autocomplete?value=${searchQuery}&type=fsli&limit=14`);
    callback(
      null,
      data.map(i => (
        { id: i.code_fsli, label: `${i.code_fsli} ${i.title}-${i.short_title}-${i.sample}-${i.synonym} ${i.nmu}` }
      )),
    );
  }
};

const addFraction = () => {
  const emptyFraction = props.tube.fractions.find(fraction => fraction.title.trim().length === 0);
  if (!emptyFraction) {
    const newFraction = {
      order: minMaxOrder.value.max + 1, tubeIdx: props.tubeidx,
    };
    emit('addFraction', newFraction);
  }
};
</script>

<style scoped lang="scss">
.tube-group {
  margin-bottom: 10px;
  background-color: #fff;
  padding: 10px 5px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 12%), 0 1px 2px rgb(0 0 0 / 24%);
  min-width: 540px;
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
::v-deep .vue-treeselect__control {
  border-collapse: separate;
}
::v-deep .treeselect-28px .vue-treeselect {
  &__control {
    height: 28px !important;
  }

  &__placeholder,
  &__single-value {
    line-height: 28px !important;
  }
}

.flex-right {
  display: flex;
  justify-content: flex-end;
}
.add-button {
  display: flex;
  width: 30px;
}
.fsli-options {
  font-size: 12px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  margin-bottom: 0
}
</style>
