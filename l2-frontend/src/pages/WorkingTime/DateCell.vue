<template>
  <div class="cell">
    <div
      v-if="props.showAdditionalButtons"
      class="additional-buttons"
    >
      <i
        v-tippy
        class="fa-solid fa-copy icon-color"
        title="Предыдущую заполненную"
        @click="copyPrevFilled"
      />
      <i
        v-tippy
        class="fa-solid fa-xmark icon-color"
        title="Очистить"
        @click="clear"
      />
    </div>
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
      :disabled="props.documentBlocked || props.workTime.blocked"
      :class="cellSelect ? 'transparentButton current-time-btn cell-select' : 'transparentButton current-time-btn'"
      @hide="updateCellSelect(false)"
      @hidden="updateTime"
      @show="updateCellSelect(true)"
    >
      <span
        class="current-time-text"
        :class="currentTime.empty ? 'opacity-text' : ''"
      >
        {{ currentTime.start }} <br> {{ currentTime.end }}
      </span>
    </button>
    <span
      v-if="props.dateTitle"
      class="opacity-text date-title"
    >
      {{ props.dateTitle }}
    </span>
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
      <div class="tp-row">
        <div class="exact-time">
          <i
            v-tippy
            class="fa-solid fa-xmark icon-color"
            title="Очистить"
            @click="clear"
          />
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
          >
          <Treeselect
            v-else
            v-model="selectedShift"
            class="treeselect-34px"
            :options="props.shiftsVariants"
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
  computed, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import moment from 'moment';
import vSelect from 'vue-select';

import RadioFieldById from '@/fields/RadioFieldById.vue';

const emit = defineEmits(['changeWorkTime', 'copyPrevFilled']);
const props = defineProps({
  workTime: {
    type: [Object, String],
    required: true,
    default: () => ({}),
  },
  employeePositionId: {
    type: Number,
    required: false,
  },
  date: {
    type: [String, undefined],
    required: true,
  },
  dateTitle: {
    type: String,
    required: false,
    default: null,
  },
  workDayStatuses: {
    type: Array,
    required: true,
    default: () => [],
  },
  shiftsVariants: {
    type: Array,
    required: true,
    default: () => [],
  },
  timeOptions: {
    type: Array,
    required: true,
    default: () => [],
  },
  documentBlocked: {
    type: Boolean,
    required: false,
    default: false,
  },
  lunchDuration: {
    type: Number,
    required: false,
    default: 0,
  },
  showAdditionalButtons: {
    type: Boolean,
    required: false,
    default: false,
  },
});

const cellSelect = ref(false);
const updateCellSelect = (select: boolean) => {
  cellSelect.value = select;
};
const startWork = ref(null);
const endWork = ref(null);
const nextDayEndWork = ref(null);
const selectedTimeOff = ref(null);
const findTimeOffLabel = () => {
  const status = props.workDayStatuses.find((type) => type.id === selectedTimeOff.value);
  if (status) {
    return status.label;
  }
  return null;
};
const selectedTimeOffLabel = ref('');

const selectedTimeOption = ref(null);

const hasChanged = (oldStartTime, oldEndTime, oldTypeId, newStartTime, newEndTime, newTypeId) => {
  const oldValues = [oldStartTime, oldEndTime, oldTypeId];
  const newValues = [newStartTime, newEndTime, newTypeId];
  return !oldValues.every((val, i) => val === newValues[i]);
};

const clear = () => {
  startWork.value = null;
  endWork.value = null;
  selectedTimeOff.value = null;
  selectedTimeOffLabel.value = '';
  nextDayEndWork.value = null;
  selectedTimeOption.value = null;
  const propsWorkTime = props.workTime;
  if (hasChanged(
    propsWorkTime.startWorkTime,
    propsWorkTime.endWorkTime,
    propsWorkTime.typeId,
    startWork.value,
    endWork.value,
    selectedTimeOff.value,
  )) {
    emit('changeWorkTime', {
      employeePositionId: props.employeePositionId,
      date: props.date,
      startWorkTime: startWork.value,
      endWorkTime: endWork.value,
      typeId: selectedTimeOff.value,
      nextDayEndWork: nextDayEndWork.value,
    });
  }
};
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
  if ((startWork.value && endWork.value) && endWork.value <= startWork.value && endWork.value !== '00:00') {
    const start = new Date(`${props.date} ${startWork.value}`);
    const endTime = endWork.value.split(':');
    nextDayEndWork.value = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 1, endTime[0], endTime[1]);
    endWork.value = '00:00';
  }
  const propsWorkTime = props.workTime;
  if (hasChanged(
    propsWorkTime.startWorkTime,
    propsWorkTime.endWorkTime,
    propsWorkTime.typeId,
    startWork.value,
    endWork.value,
    selectedTimeOff.value,
  )) {
    emit('changeWorkTime', {
      employeePositionId: props.employeePositionId,
      date: props.date,
      startWorkTime: startWork.value,
      endWorkTime: endWork.value,
      typeId: selectedTimeOff.value,
      nextDayEndWork: nextDayEndWork.value,
    });
    nextDayEndWork.value = null;
  }
};

watch([startWork, endWork], () => {
  if (startWork.value && endWork.value && selectedTimeOff.value) {
    selectedTimeOff.value = null;
    selectedTimeOffLabel.value = '';
  }
});

const endTimeVariants = ref([
  { id: 'shift', label: 'Смена' },
  { id: 'time', label: 'Конец' },
]);
const selectedEndVariant = ref('shift');
const selectedShift = ref(null);

watch(selectedShift, () => {
  if (selectedShift.value) {
    const start = new Date(`${props.date} ${startWork.value}`);
    const shiftInMinutes = Number(selectedShift.value) * 60;
    const shiftWithLunch = shiftInMinutes + props.lunchDuration;
    const end = new Date(start.getTime() + (shiftWithLunch * 60 * 1000));
    if (end.getDate() > start.getDate()) {
      endWork.value = '00:00';
      nextDayEndWork.value = end;
    } else {
      endWork.value = moment(end).format('HH:mm');
    }
  }
});

const currentTime = computed(() => {
  if (startWork.value && !endWork.value) {
    return { start: startWork.value, end: '--:--', empty: false };
  }
  if (startWork.value && endWork.value) {
    return { start: startWork.value, end: endWork.value, empty: false };
  }
  if (selectedTimeOff.value) {
    return { start: selectedTimeOffLabel.value, end: '', empty: false };
  }
  return { start: '--:--', end: '--:--', empty: true };
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

const copyPrevFilled = () => {
  emit('copyPrevFilled', { date: props.date });
};

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
  white-space: normal;
}
.current-time-btn {
  width: 100%;
  height: 42px;
  padding: 1px 0;
}
.opacity-text {
  opacity: 0.3;
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
.icon-color {
  color: #636e7e;
}
.cell {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0
}
.date-title {
  margin: 0 auto;
  white-space: normal;
}
.additional-buttons {
  display: flex;
  gap: 5px;
  margin: 0 auto;
}
</style>
