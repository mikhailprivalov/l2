<template>
  <Treeselect
    ref="treeselect"
    v-model="selectedItem"
    v-tippy
    :options="props.optionsList"
    placeholder="Ед. изм."
    :clearable="false"
    :disabled="props.hide"
    class="treeselect-28px"
    :append-to-body="true"
    :title="title"
    @input="inputValue"
  />
</template>

<script setup lang="ts">
import {
  onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const props = defineProps({
  selectItem: {
    type: null,
    required: true,
  },
  optionsList: {
    type: Array,
    required: true,
  },
  rowIndex: {
    type: Number,
    required: false,
  },
  hide: {
    type: Boolean,
    required: false,
  },
});

const emit = defineEmits(['inputValue']);

const treeselect = ref(null);
const selectedItem = ref(-1);
const title = ref('');

const appendValue = () => {
  selectedItem.value = props.selectItem;
  if (selectedItem.value) {
    const res = props.optionsList.find(unit => unit.id === selectedItem.value);
    if (res) {
      title.value = res.label;
    }
  } else {
    title.value = '';
    treeselect.value.$el.removeAttribute('data-original-title');
  }
};

watch(() => props.selectItem, () => {
  appendValue();
});

const inputValue = () => {
  if (selectedItem.value !== props.selectItem) {
    emit('inputValue', { selectedItem: selectedItem.value, rowIndex: props.rowIndex });
  }
};
onMounted(() => {
  appendValue();
});
</script>

<style scoped lang="scss">

</style>
