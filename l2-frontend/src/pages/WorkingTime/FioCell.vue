<template>
  <div class="fio">
    <div class="top-icons">
      <i
        ref="transfer"
        v-tippy="{
          html: `#tempTransferTo${props.employeePositionId}`,
          arrow: true,
          reactive: true,
          interactive: true,
          animation: 'fade',
          duration: 0,
          theme: 'light',
          placement: 'bottom',
          trigger: 'click',
        }"
        class="fa-solid fa-arrow-right icon-color"
      />
    </div>
    <VueTippyDiv
      :tag="props.tag"
      :text="props.text"
      :tippy-max-width="props.tippyMaxWidth"
      class="fio-text"
    />
    <div
      :id="`tempTransferTo${props.employeePositionId}`"
      class="tp"
    >
      <div class="date-transfer">
        <input
          v-model="dateTransfer"
          class="form-control"
          type="date"
        >
        <button
          class="btn btn-blue-nb"
          @click="employeeTransfer"
        >
          <i class="fa fa-save" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import { ref } from 'vue';

import VueTippyDiv from '@/pages/ManageChambers/components/VueTippyDiv.vue';

const emit = defineEmits(['employeeTransfer']);

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
  employeePositionId: {
    type: Number,
    required: true,
  },
});

const dateTransfer = ref(null);

const employeeTransfer = () => {
  emit('employeeTransfer', { employeePositionId: props.employeePositionId, date: dateTransfer.value });
};
</script>

<style scoped lang="scss">
.fio {
  height: 100%;
}
.top-icons {
  display: flex;
  justify-content: flex-end;
  gap: 5px;
}
.fio-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  height: 48px;
  padding-top: 7px;
}
.tp {
  height: auto;
  width: 180px;
}
.icon-color {
  color: #636e7e;
}
.date-transfer {
  display: flex;
  gap: 5px;
}
</style>
