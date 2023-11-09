<template>
  <div class="flex">
    <Treeselect
      v-model="selectTemplate"
      :options="templatesWorkTime"
      value-format="object"
      :append-to-body="true"
      placeholder="Выберите время"
      @input="changeWorkTime"
    />
    <button class="transparentButton">
      <i
        class="fa fa-clock-o"
        aria-hidden="true"
      />
    </button>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
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
});

const workTimeIsFilled = computed(() => !!(typeof props.workTime === 'object' && props.workTime.startWorkTime
  && props.workTime.endWorkTime));

const selectTemplate = ref(null);
const templatesWorkTime = ref([
  { id: 1, label: '8:00-16:30' },
  { id: 2, label: '8:00-15:48' },
  { id: 3, label: '15:48-24:00' },
]);

const appendCurrentTime = () => {
  if (workTimeIsFilled.value) {
    const start = props.workTime.startWorkTime;
    const end = props.workTime.endWorkTime;
    const workTimeLabel = `${start}-${end}`;
    const templateCurrentWorkTime = templatesWorkTime.value.find((template) => template.label === workTimeLabel);
    if (templateCurrentWorkTime) {
      selectTemplate.value = templateCurrentWorkTime;
    } else {
      const currentWorkTime = { id: templatesWorkTime.value.length + 1, label: workTimeLabel };
      templatesWorkTime.value.push(currentWorkTime);
      selectTemplate.value = currentWorkTime;
    }
  }
};

const changeWorkTime = () => {
  if (selectTemplate.value) {
    const workTime = selectTemplate.value?.label?.split('-');
    const start = workTime[0];
    const end = workTime[1];
    if (start !== props.workTime.startWorkTime || end !== props.workTime.endWorkTime) {
      emit('changeWorkTime', {
        start, end, rowIndex: props.rowIndex, columnKey: props.columnKey,
      });
    }
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
  width: 176px
}
.transparentButton {
  background-color: transparent;
  color: #434A54;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
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
</style>
