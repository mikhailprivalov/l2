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
      class="transparentButton current-time-width"
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
          v-for="variant in workTimeVariants"
          :key="variant.id"
          class="variant"
          :class="activeVariant === variant.id && 'active'"
          @click="selectVariant(variant.id)"
        >
          {{ `${variant.startWork}-${variant.endWork}` }}
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
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance, ref, watch,
} from 'vue';

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

const activeVariant = ref(null);
const workTimeVariants = ref([
  { id: 1, startWork: '08:00', endWork: '16:30' },
  { id: 2, startWork: '08:00', endWork: '15:48' },
  { id: 3, startWork: '15:48', endWork: '00:00' },
  { id: 4, startWork: '19:48', endWork: '21:00' },
  { id: 5, startWork: '14:48', endWork: '16:00' },
]);

const selectVariant = (variantId) => {
  activeVariant.value = variantId;
};

const startWork = ref(null);
const endWork = ref(null);

const currentTime = computed(() => {
  if (startWork.value && endWork.value) {
    return `${startWork.value}\n${endWork.value}`;
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
  height: 120px;
  width: 254px;
}

.tp-row {
  display: flex;
  flex-wrap: wrap;
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
.current-time-width {
  width: 50px;
}
</style>
