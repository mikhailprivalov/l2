<template>
  <div class="flex">
    <Treeselect
      v-model="selectTemplate"
      :options="templatesWorkTime"
      value-format="object"
      :append-to-body="true"
      placeholder="Выберите время"
      class="time-width"
      @input="changeWorkTime"
    />
    <button
      v-if="!props.isFirstDay"
      v-tippy
      class="transparentButton"
      title="Скопировать предыдущий"
      @click="copyPrevTime"
    >
      <i class="fa-solid fa-copy" />
    </button>
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
      class="transparentButton"
    >
      <i
        class="fa fa-clock-o"
        aria-hidden="true"
      />
    </button>

    <div
      id="temp"
      class="tp"
    >
      <div>
        <label class="tp-label">Начало</label>
        <input
          v-model="startWork"
          class="form-control"
          type="time"
          :max="endWork"
        >
      </div>
      <div>
        <label class="tp-label">Конец</label>
        <input
          v-model="endWork"
          class="form-control"
          type="time"
          :min="startWork"
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
</template>

<script setup lang="ts">
import {
  computed, getCurrentInstance,
  onMounted, ref,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const emit = defineEmits(['changeWorkTime']);
const props = defineProps({
  workTime: {
    type: [Object, String],
    required: true,
  },
  rowIndex: {
    type: Number,
    required: true,
  },
  columnKey: {
    type: String,
    required: true,
  },
  isFirstDay: {
    type: Boolean,
    required: true,
  },
  prevWorkTime: {
    type: [Object, String],
    required: false,
  },
});

const propsWorkTimeIsFilled = computed(() => !!(typeof props.workTime === 'object' && props.workTime.startWorkTime
  && props.workTime.endWorkTime));

const selectTemplate = ref(null);
const templatesWorkTime = ref([
  { id: 1, label: '08:00-16:30' },
  { id: 2, label: '08:00-15:48' },
  { id: 3, label: '15:48-00:00' },
]);
const root = getCurrentInstance().proxy.$root;

const createLabel = (start, end) => `${start}-${end}`;

const changeTemplate = (templateLabel: string) => {
  const templateCurrentWorkTime = templatesWorkTime.value.find((template) => template.label === templateLabel);
  if (templateCurrentWorkTime) {
    selectTemplate.value = templateCurrentWorkTime;
  } else {
    const currentWorkTime = { id: templatesWorkTime.value.length + 1, label: templateLabel };
    templatesWorkTime.value.push(currentWorkTime);
    selectTemplate.value = currentWorkTime;
  }
};

const startWork = ref(null);
const endWork = ref(null);

const appendCurrentTime = () => {
  if (propsWorkTimeIsFilled.value) {
    const workTimeLabel = createLabel(props.workTime.startWorkTime, props.workTime.endWorkTime);
    changeTemplate(workTimeLabel);
  }
};

const changeWorkTime = () => {
  if (selectTemplate.value) {
    const workTime = selectTemplate.value?.label?.split('-');
    const [start, end] = workTime;
    if (start !== startWork.value || end !== endWork.value) {
      startWork.value = start;
      endWork.value = end;
    }
    if (startWork.value !== props.workTime.startWorkTime || endWork.value !== props.workTime.endWorkTime) {
      emit('changeWorkTime', {
        start: startWork.value, end: endWork.value, rowIndex: props.rowIndex, columnKey: props.columnKey, clear: false,
      });
    }
  } else {
    startWork.value = null;
    endWork.value = null;
    emit('changeWorkTime', {
      start: startWork.value, end: endWork.value, rowIndex: props.rowIndex, columnKey: props.columnKey, clear: true,
    });
  }
};

const timeCorrect = computed(() => !!(startWork.value && endWork.value) && (startWork.value < endWork.value));
const changeExact = () => {
  if (timeCorrect.value) {
    const workTimeLabel = `${startWork.value}-${endWork.value}`;
    if (selectTemplate.value) {
      if (workTimeLabel !== selectTemplate.value.label) {
        changeTemplate(workTimeLabel);
      } else {
        root.$emit('msg', 'error', 'Время уже назначено');
      }
    } else {
      changeTemplate(workTimeLabel);
    }
  } else if (!startWork.value || !endWork.value) {
    root.$emit('msg', 'error', 'Время не заполнено');
  } else if (startWork.value >= endWork.value) {
    root.$emit('msg', 'error', 'Время не верно');
  }
};

const copyPrevTime = () => {
  if (props.prevWorkTime) {
    const workTimeLabel = createLabel(props.prevWorkTime.startWorkTime, props.prevWorkTime.endWorkTime);
    changeTemplate(workTimeLabel);
  }
};
onMounted(() => {
  appendCurrentTime();
});
</script>

<style scoped lang="scss">
.flex {
  display: flex;
  flex-wrap: nowrap;
}
.time-width {
  width: 138px
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
.tp-button {
  width: 35px;
  height: 34px;
  margin-top: 24px;
}
.tp-label {
  height: 19px;
}
.tp {
  display: flex;
  height: 60px;
  width: 223px;
}
</style>
