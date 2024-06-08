<template>
  <div class="root">
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
      class="transparentButton current-time-wh"
    >
      <!-- eslint-disable vue/singleline-html-element-content-newline -->
      <p class="current-time-text">{{ currentTime }}</p>
      <!-- eslint-enable -->
    </button>
    <button
      v-tippy
      class="transparentButton"
      title="Скопировать предыдущий"
      @click="copyPrevTime"
    >
      <i class="fa-solid fa-copy" />
    </button>

    <div
      id="temp"
      class="tp"
    >
      <div class="tp-row">
        <div
          v-for="option in timeOptions"
          :key="option.id"
          class="variant"
          :class="selectedTimeOption === option.id && 'active'"
          @click="selectTime(option.id, option.startWork, option.endWork)"
        >
          {{ `${option.startWork}-${option.endWork}` }}
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
          <label class="tp-label">Конец</label>
          <input
            v-model="endWork"
            class="form-control"
            type="time"
          >
        </div>
        <button
          v-tippy
          class="transparentButton tp-button"
          title="Сохранить"
          @click="changeExact"
        >
          <i class="fa-solid fa-save" />
        </button>
      </div>
      <div class="tp-row">
        <RadioFieldById
          v-model="selectedTimeOff"
          :variants="typesTimeOff"
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

import RadioFieldById from '@/fields/RadioFieldById.vue';

const emit = defineEmits(['changeWorkTime']);
const props = defineProps({
  workTime: {
    type: [Object, String],
    required: true,
    default: '',
  },
  rowIndex: {
    type: Number,
    required: true,
  },
  columnKey: {
    type: String,
    required: true,
  },
});

const root = getCurrentInstance().proxy.$root;

const startWork = ref(null);
const endWork = ref(null);

const selectedTimeOption = ref(null);
const timeOptions = ref([
  { id: 1, startWork: '08:00', endWork: '16:30' },
  { id: 2, startWork: '08:00', endWork: '15:48' },
  { id: 3, startWork: '15:48', endWork: '00:00' },
  { id: 4, startWork: '19:48', endWork: '21:00' },
  { id: 5, startWork: '14:48', endWork: '16:00' },
]);
const selectedTimeOff = ref(null);
const typesTimeOff = ref([
  { id: 1, label: 'А' },
  { id: 2, label: 'Б' },
  { id: 3, label: 'В' },
  { id: 4, label: 'Г' },
  { id: 5, label: 'Д' },
  { id: 6, label: 'Е' },
]);
const selectedTypeLabel = ref('');
const selectTime = (variantId: number, startTime: string, endTime: string) => {
  selectedTimeOption.value = variantId;
  startWork.value = startTime;
  endWork.value = endTime;
};

const timeOff = () => {
  selectedTypeLabel.value = typesTimeOff.value.find((type) => type.id === selectedTimeOff.value).label;
  startWork.value = null;
  endWork.value = null;
  selectedTimeOption.value = null;
};

watch([startWork, endWork], () => {
  if (startWork.value && endWork.value && selectedTimeOff.value) {
    selectedTimeOff.value = null;
    selectedTypeLabel.value = '';
  }
});

const currentTime = computed(() => {
  if (startWork.value && endWork.value) {
    return `${startWork.value}\n${endWork.value}`;
  } if (selectedTimeOff.value) {
    return selectedTypeLabel.value;
  }
  return '--:--\n--:--';
});

const appendCurrentTime = () => {
  startWork.value = props.workTime.startWorkTime;
  endWork.value = props.workTime.endWorkTime;
};

const changeExact = () => {
  if ((startWork.value && endWork.value) && ((startWork.value < endWork.value) || (startWork.value > endWork.value
    && endWork.value === '00:00'))) {
    emit('changeWorkTime', {
      start: startWork.value, end: endWork.value, rowIndex: props.rowIndex, columnKey: props.columnKey,
    });
  } else if (startWork.value >= endWork.value) {
    root.$emit('msg', 'error', 'Время не верно');
  }
};

const copyPrevTime = () => {
  if (props.prevWorkTime) {
    root.$emit('msg', 'ok', 'Скопировано');
  }
};

watch(() => props.workTime, () => {
  appendCurrentTime();
}, { immediate: true });

</script>

<style scoped lang="scss">
.root {
  display: flex;
  flex-wrap: nowrap;
}
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
  background-color: #37BC9B;
  color: #FFFFFF;
}
button[disabled] {
  cursor: default;
  background-color: transparent !important;
  color: grey !important;
}
.tp-button {
  width: 35px;
  height: 34px;
  margin-top: 24px;
}
.tp {
  height: 150px;
  width: 254px;
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

  &:hover {
    background-color: #f5f5f5;
  }
  &.active {
      background-color: #d9f1d7;
  }
}
.current-time-text {
  margin: 0;
}
.current-time-wh {
  width: 50px;
  height: 42px;
}
</style>
