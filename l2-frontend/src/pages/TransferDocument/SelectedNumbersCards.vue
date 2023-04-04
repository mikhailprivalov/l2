<template>
  <div>
    <table class="table table-bordered no-first-border-top">
      <colgroup>
        <col>
        <col width="28">
      </colgroup>
      <thead>
        <tr>
          <th class="text-center">
            Номер карты
          </th>
          <th class="text-center">
            Кабинет
          </th>
          <th class="nopd noel">
            <input
              type="checkbox"
            >
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in cards"
          :key="row.pk"
        >
          <td class="text-center">
            {{ row.number }}
          </td>
          <td class="text-center">
            {{ row.room }}
          </td>
          <td class="nopd">
            <input
              v-model="row.checked"
              type="checkbox"
            >
          </td>
        </tr>
      </tbody>
    </table>
    <button
      class="btn btn-blue-nb nbr"
      :class="$style.createButton"
      @click="execute"
    >
      {{ props.addText || '' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  isPendAccept?: boolean,
  isCurrent?: boolean,
  isTransferCard?: boolean,
  addText?: string,
  all_checked: boolean
}>();
const cards = [
  { pk: 1, number: '121212', room: '24' },
  { pk: 2, number: '343', room: '25' },
  { pk: 3, number: '343', room: '26' },
];
</script>

<style lang="scss" module>
.root {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

.createButton {
  height: 34px;
  width: 100%;
  margin: 5px;
  position: absolute;
  bottom: 0;
  right: 0;
  left: 0;
}

.editButton {
  cursor: pointer;
  color: #56616c;
  float: right;
  display: inline-block;
  padding: 3px;
  margin-top: -3px;

  &:hover {
    color: #049372;
  }
}

.listItemSelected, .listItemNotActive {
  .editButton {
    opacity: .6;
    color: #ffffff;

    &:hover {
      color: #ffffff;
      opacity: 1;
    }
  }
}
</style>
