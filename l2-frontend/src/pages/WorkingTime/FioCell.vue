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
        class="fa-solid fa-arrow-circle-o-right icon-color"
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
      <input
        class="form-control"
        type="date"
      >
    </div>
  </div>
</template>

<script setup lang="ts">

import VueTippyDiv from '@/pages/ManageChambers/components/VueTippyDiv.vue';

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
  width: 150px;
}
.icon-color {
  color: #636e7e;
}
</style>
