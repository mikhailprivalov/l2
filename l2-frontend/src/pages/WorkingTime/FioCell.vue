<template>
  <div class="fio">
    <div class="top-icons">
      <i
        ref="transfer"
        v-tippy="popover(`#tempTransferTo${props.employeePositionId}`)"
        class="fa-solid fa-arrow-right icon-color"
      />
    </div>
    <div
      v-tippy="{ maxWidth: props.tippyMaxWidth }"
      :title="fioTooltip"
      class="fio-text"
    >
      {{ props.text }}
    </div>
    <div
      :id="`tempTransferTo${props.employeePositionId}`"
      class="tp"
    >
      <div class="date-transfer">
        <input
          v-model="dateTransfer"
          class="form-control"
          type="date"
        >
        <button
          class="btn btn-blue-nb"
          @click="employeeTransfer"
        >
          <i class="fa fa-save" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import { computed, ref } from 'vue';

import popover from '@/pages/WorkingTime/utils/tippy';

const emit = defineEmits(['employeeTransfer']);

const props = defineProps({
  text: {
    type: [String, undefined, null],
    required: true,
  },
  tabelNumber: {
    type: [String, undefined, null],
    required: false,
    default: '',
  },
  tippyMaxWidth: {
    type: String,
    required: false,
  },
  employeePositionId: {
    type: Number,
    required: true,
  },
});

const fioTooltip = computed(() => {
  const tabel = props.tabelNumber
    ? `Таб. №: ${props.tabelNumber}`
    : 'Таб. № не указан';
  return `${props.text}<br>${tabel}`;
});

const dateTransfer = ref(null);
const transfer = ref(null);

const employeeTransfer = () => {
  emit('employeeTransfer', { employeePositionId: props.employeePositionId, date: dateTransfer.value });
  dateTransfer.value = null;
  // eslint-disable-next-line no-underscore-dangle
  transfer.value._tippy.hide();
};
</script>

<style scoped lang="scss">
.fio {
  height: 100%;
}
.top-icons {
  display: flex;
  justify-content: flex-end;
  gap: 5px;
}
.fio-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  height: 48px;
  padding-top: 7px;
}
.tp {
  height: auto;
  width: 180px;
}
.icon-color {
  color: #636e7e;
}
.date-transfer {
  display: flex;
  gap: 5px;
}
</style>
