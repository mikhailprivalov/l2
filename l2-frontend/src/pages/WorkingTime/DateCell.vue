<template>
  <div>
    <Treeselect
      v-model="selectTemplate"
      :options="templatesWorkTime"
      value-format="object"
      :append-to-body="true"
      @input="changeTemplate"
    />
  </div>
</template>

<script setup lang="ts">
import {
  computed, defineComponent, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const emit = defineEmits(['changeWorkTime']);
const props = defineProps({
  workTime: {
    type: Object,
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

const selectTemplate = ref(null);
const templatesWorkTime = ref([
  { id: 1, label: '8:00-16:30' },
  { id: 2, label: '8:00-15:48' },
]);
const data = ref('');

const timeStart = ref('');
const timeEnd = ref('');
const appendCurrentTemplates = () => {
  const start = props.workTime.startWorkTime;
  const end = props.workTime.endWorkTime;
  const currentWorkTime = { id: 3, label: `${start}-${end}` };
  templatesWorkTime.value.push(currentWorkTime);
  selectTemplate.value = currentWorkTime;
};
const changeTemplate = () => {
  if (selectTemplate.value) {
    console.log('мы зашли в проверку1');
    const workTime = selectTemplate.value?.label?.split('-');
    const start = workTime[0];
    const end = workTime[1];
    console.log(start, props.workTime.startWorkTime);
    console.log(end, props.workTime.endWorkTime);
    if (start !== props.workTime.startWorkTime || end !== props.workTime.endWorkTime) {
      emit('changeWorkTime', {
        start, end, rowIndex: props.rowIndex, columnKey: props.columnKey,
      });
    }
  }
};

onMounted(() => {
  appendCurrentTemplates();
});
</script>

<style scoped lang="scss">
.main {
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
}
.input-hour {
  width: 100%;
  flex-grow: 1;
}
.tp {
  min-height: 400px;
  text-align: left;
  padding: 1px;

  table {
    margin: 0;
  }

  max-height: 700px;
  width: 900px;
  overflow-y: auto;

  &-inner {
    overflow: visible;
  }
}
</style>
