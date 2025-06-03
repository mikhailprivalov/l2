<template>
  <div class="position">
    <div class="top-icons">
      <i
        v-tippy
        class="fa-solid fa-copy icon-color"
        title="Сверху"
        @click="copyTop"
      />
      <i
        ref="from"
        v-tippy="{
          html: `#tempCopyFrom${props.employeePositionId}`,
          arrow: true,
          reactive: true,
          interactive: true,
          animation: 'fade',
          duration: 0,
          theme: 'light',
          placement: 'bottom',
          trigger: 'click',
        }"
        class="fa-solid fa-paste icon-color"
      />
      <i
        v-tippy
        class="fa-solid fa-xmark icon-color"
        title="Очистить"
        @click="clear"
      />
    </div>
    <VueTippyDiv
      :tag="props.tag"
      :text="props.text"
      :tippy-max-width="props.tippyMaxWidth"
      class="position-text"
    />
    <div
      :id="`tempCopyFrom${props.employeePositionId}`"
      class="tp"
    >
      <Treeselect
        v-model="selectedEmployeePositionId"
        class="treeselect-34px"
        :options="props.employeePositions"
        placeholder="Работник"
        :normalizer="normalizer"
        :clearable="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import VueTippyDiv from '@/pages/ManageChambers/components/VueTippyDiv.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

const props = defineProps({
  text: {
    type: [String, undefined, null],
    required: true,
  },
  tippyMaxWidth: {
    type: String,
    required: false,
  },
  tag: {
    type: String,
    required: false,
    default: 'div',
  },
  rowIndex: {
    type: Number,
    required: true,
  },
  employeePositionId: {
    type: Number,
    required: true,
  },
  employeePositions: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(['copyTop', 'copyFrom', 'clear']);
const copyTop = () => {
  if (props.rowIndex !== 0) {
    emit('copyTop', { rowIndex: props.rowIndex });
  }
};

const from = ref(null);
const selectedEmployeePositionId = ref(null);
const copyFrom = () => {
  emit('copyFrom', {
    employeePositionId: props.employeePositionId,
    selectedEmployeePositionId:
    selectedEmployeePositionId.value,
  });
};

watch(selectedEmployeePositionId, () => {
  if (selectedEmployeePositionId.value) {
    copyFrom();
    selectedEmployeePositionId.value = null;
    // eslint-disable-next-line no-underscore-dangle
    from.value._tippy.hide();
  }
});
const normalizer = (node) => ({
  id: node.employeePositionId,
  label: node.fio,
});
const clear = () => {
  emit('clear', { rowIndex: props.rowIndex });
};
</script>

<style scoped lang="scss">
.position {
  height: 100%;
}
.text {
  margin: 0;
}
.top-icons {
  display: flex;
  justify-content: flex-end;
  gap: 5px;
}
.position-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  height: 48px;
  padding-top: 7px;
}
.tp {
  height: auto;
  width: 150px;
}
.icon-color {
  color: #636e7e;
}
</style>
