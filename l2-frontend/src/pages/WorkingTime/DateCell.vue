<template>
  <div>
    <button ref="btn">
      fff
    </button>
  </div>
</template>

<script setup lang="ts">
import {
  computed, defineComponent, reactive, ref, watch,
} from 'vue';
import { useTippy } from './vue-tippy';

const props = defineProps({
  text: {
    type: String,
    required: true,
  },
});
const btn = ref(null);
const options = reactive({
  content: 'reactive',
  placement: 'top',
});
useTippy(btn, options);
const data = ref('');

const timeStart = ref('');
const timeEnd = ref('');

watch([timeStart, timeEnd], (newData, prevData) => {
  console.log(prevData);
  console.log(newData);
  data.value = `${newData[0]}-${newData[1]}`;
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
