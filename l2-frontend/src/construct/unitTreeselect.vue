<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import Treeselect, { ASYNC_SEARCH } from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const props = defineProps({
  select: {
    type: [Number || null],
    required: true,
  },
  option: {
    type: Array,
    required: true,
  },
});
const treeselect = ref(null);
const data2 = ref(-1);
const title = ref('');

watch(() => props.select, () => {
  data2.value = props.select;
  if (data2.value) {
    const res = props.option.find(unit => unit.id === data2.value);
    if (res) {
      title.value = res.label;
    } else {
      title.value = '';
    }
  } else {
    title.value = '';
    console.log(treeselect.value.$el.getAttribute('data-original-title'));
    treeselect.value.$el.removeAttribute('data-original-title');
    console.log(treeselect.value.$el.getAttribute('data-original-title'));
  }
}, { immediate: true });

const change = () => {
  if (data2.value) {
    const res = props.option.find(unit => unit.id === data2.value);
    if (res) {
      title.value = res.label;
    } else {
      title.value = '';
    }
  } else {
    title.value = '';
  }
};
// const showTitle = (event) {
//       if (event.target.scrollWidth > event.target.clientWidth) {
//       } else {
//         this.show = false;
//         event.target.removeAttribute('data-original-title');
//       }
//     },
</script>

<template>
  <Treeselect
    v-model="data2"
    v-tippy
    :options="props.option"
    placeholder="Ед. изм."
    :clearable="false"
    class="treeselect-28px"
    :append-to-body="true"
    :title="title"
    @input="change"
    ref="treeselect"
  />
</template>

<style scoped lang="scss">

</style>
