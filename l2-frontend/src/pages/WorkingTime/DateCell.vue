<template>
  <div>
    <Treeselect
      v-model="selectTemplate"
      :options="templatesWorkTime"
      @change=""
    />
  </div>
</template>

<script setup lang="ts">
import {
  computed, defineComponent, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const props = defineProps({
  workTime: {
    type: Object,
    required: true,
  },
});

const selectTemplate = ref(-1);
const templatesWorkTime = ref([
  { id: 1, label: '8:00-16:30' },
  { id: 2, label: '8:00-15:48' },
]);
const data = ref('');

const timeStart = ref('');
const timeEnd = ref('');
const appendTemplates = () => {
  const start = props.workTime.startWorkTime;
  const end = props.workTime.endWorkTime;
  templatesWorkTime.value.push({ id: 3, label: `${start}-${end}` });
  selectTemplate.value = 3;
};
onMounted(() => {
  appendTemplates();
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
