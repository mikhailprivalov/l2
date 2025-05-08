<template>
  <div>
    <button
      v-tippy="{
        html: '#temp',
        arrow: true,
        reactive: true,
        interactive: true,
        animation: 'fade',
        duration: 0,
        theme: 'light',
        placement: 'bottom',
        trigger: 'click',
      }"
      :disabled="props.disabled"
      :class="cellSelect ? 'transparentButton current-time-wh cell-select' : 'transparentButton current-time-wh'"
      @hide="updateCellSelect(false)"
      @hidden="updateTime"
      @show="updateCellSelect(true)"
    >
      <!-- eslint-disable vue/singleline-html-element-content-newline -->
      <p
        class="current-time-text"
        :class="currentTime.empty ? 'opacity-text' : ''"
      >{{ currentTime.text }}</p>
      <!-- eslint-enable -->
    </button>
    <div
      id="temp"
      class="tp"
    >
      <div class="tp-row">
        <div
          v-for="option in props.timeOptions"
          :key="option.id"
          class="variant"
          :class="selectedTimeOption === option.id && 'active'"
          @click="selectTime(option.id, option.start, option.end)"
        >
          {{ `${option.start}-${option.end}` }}
        </div>
      </div>
      <div class="tp-row space-between">
        <div class="copy-text">Прошлые</div>
        <div class="margin-left-right">
          <input
            v-model="countDaysCopy"
            class="form-control copy-count"
            type="number"
            min="1"
            max="31"
          >
        </div>
        <div class="copy-text">дней</div>
        <div class="margin-left-right">
          <button class="btn btn-blue-nb copy-button">Скопировать</button>
        </div>
      </div>
      <div class="tp-row">
        <div class="exact-time">
          <label class="tp-label">Начало</label>
          <input
            v-model="startWork"
            class="form-control"
            type="time"
          >
        </div>
        <div class="exact-time">
          <RadioFieldById
            v-model="selectedEndVariant"
            :variants="endTimeVariants"
            class="end-variants"
          />
          <input
            v-if="selectedEndVariant === 'time'"
            v-model="endWork"
            class="form-control"
            type="time"
            max="23:59"
          >
          <Treeselect
            v-else
            v-model="selectedShift"
            class="treeselect-34px"
            :options="shifts"
            :disabled="!startWork"
            placeholder="Смена"
          />
        </div>
      </div>
      <div class="tp-row">
        <RadioFieldById
          v-model="selectedTimeOff"
          :variants="props.workDayStatuses"
          :start-null="true"
          @modified="timeOff"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import RadioFieldById from '@/fields/RadioFieldById.vue';

const emit = defineEmits(['changeWorkTime']);
const props = defineProps({
  workTime: {
    type: [Object, String],
    required: true,
    default: '',
  },
  employeePositionId: {
    type: Number,
    required: true,
  },
  date: {
    type: [String, undefined],
    required: true,
  },
  workDayStatuses: {
    type: Array,
    required: true,
  },
  timeOptions: {
    type: Array,
    required: true,
  },
  disabled: {
    type: Boolean,
    required: false,
  },
});

const root = getCurrentInstance().proxy.$root;

const cellSelect = ref(false);
const updateCellSelect = (select: boolean) => {
  cellSelect.value = select;
};
const startWork = ref(null);
const endWork = ref(null);
const selectedTimeOff = ref(null);
const findTimeOffLabel = () => {
  const status = props.workDayStatuses.find((type) => type.id === selectedTimeOff.value);
  if (status) {
    return status.label;
  }
  return null;
};
const selectedTimeOffLabel = ref('');

const timeValid = () => {
  if (startWork.value > endWork.value && !selectedTimeOff.value) {
    startWork.value = '';
    endWork.value = '';
    return { valid: false, reason: 'Время начала больше времени конца' };
  }
  return { valid: true, reason: '' };
};

const selectedTimeOption = ref(null);

const selectTime = (variantId: number, startTime: string, endTime: string) => {
  selectedTimeOption.value = variantId;
  startWork.value = startTime;
  endWork.value = endTime;
};

const countDaysCopy = ref(1);
watch(countDaysCopy, () => {
  if (countDaysCopy.value < 1) {
    countDaysCopy.value = 1;
  } else if (countDaysCopy.value > 31) {
    countDaysCopy.value = 31;
  }
});

const timeOff = () => {
  selectedTimeOffLabel.value = findTimeOffLabel();
  startWork.value = null;
  endWork.value = null;
  selectedTimeOption.value = null;
};

const updateTime = async () => {
  const { valid, reason } = timeValid();
  if (!valid) {
    root.$emit('msg', 'error', reason);
  } else {
    emit('changeWorkTime', {
      employeePositionId: props.employeePositionId,
      date: props.date,
      startWorkTime: startWork.value,
      endWorkTime: endWork.value,
      typeId: selectedTimeOff.value,
    });
  }
};

watch([startWork, endWork], () => {
  if (startWork.value && endWork.value && selectedTimeOff.value) {
    selectedTimeOff.value = null;
    selectedTimeOffLabel.value = '';
  }
});

watch(endWork, () => {
  if (endWork.value === '00:00') {
    endWork.value = '23:59';
  }
});

const endTimeVariants = ref([
  { id: 'time', label: 'Конец' },
  { id: 'shift', label: 'Смена' },
]);
const selectedEndVariant = ref('time');

const shifts = ref([
  { id: '8', label: '8 ч.' },
  { id: '7.8', label: '7.8 ч.' },
  { id: '16', label: '16 ч.' },
  { id: '16.2', label: '16.2 ч.' },
]);
const selectedShift = ref(null);

const currentTime = computed(() => {
  if (startWork.value && endWork.value) {
    return { text: `${startWork.value}\n${endWork.value}`, time: true };
  } if (selectedTimeOff.value) {
    return { text: selectedTimeOffLabel.value, timeOff: true };
  }
  return { text: '--:--\n--:--', empty: true };
});

const appendCurrentTime = () => {
  startWork.value = props.workTime.startWorkTime;
  endWork.value = props.workTime.endWorkTime;
  selectedTimeOff.value = props.workTime.typeId;
  selectedTimeOffLabel.value = findTimeOffLabel();
  selectedTimeOption.value = null;
};

watch(() => props.workTime, () => {
  appendCurrentTime();
}, { immediate: true });

</script>

<style scoped lang="scss">
.time-width {
  margin: 0;
}
.transparentButton {
  background-color: transparent;
  color: #434A54;
  border: none;
  border-radius: 4px;
}
.transparentButton:hover {
  background-color: #434a54;
  color: #FFFFFF;
  border: none;
}
.transparentButton:active {
  background-color: #1061bb;
  color: #FFFFFF;
}
.cell-select {
  background-color: #434a54;
  color: #FFFFFF;
}
button[disabled] {
  cursor: default;
  background-color: transparent !important;
  color: grey !important;
}
.tp {
  height: auto;
  width: 280px;
}

.tp-row {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 2px;
}
.tp-label {
  height: 19px;
}
.exact-time {
  flex: 1;
}
.variant {
  background-color: #FFF;
  font-weight: bold;
  margin: 1px 2px;
  padding: 0 1px;
  border: 1px solid grey;
  border-radius: 6px;
  flex: 30%;

  &:hover {
    background-color: #f5f5f5;
  }
  &.active {
      background-color: #ddf3fe;
  }
}
.current-time-text {
  margin: 0;
}
.current-time-wh {
  width: 100%;
  height: 42px;
}
.opacity-text {
  opacity: 0.3;
}
.margin-left-right {
  margin-left: 2px;
  margin-right: 2px;
}
.copy-button {
  padding: 3px;
}
.copy-count {
  padding: 0 6px;
  height: 28px;
}
.copy-text {
  padding: 4px 0;
}
.space-between {
  justify-content: space-between;
}
.end-variants {
  height: 19px;
  margin-bottom: 5px;
}
::v-deep .vue-treeselect__control {
  border-color: #aab2bd;
}
</style>
