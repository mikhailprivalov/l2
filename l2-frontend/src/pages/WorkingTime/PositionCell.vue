<template>
  <div class="position">
    <div class="top-icons">
      <i
        v-tippy
        class="fa-solid fa-copy"
        title="Сверху"
        @click="action('copyTop')"
      />
      <i
        v-tippy
        class="fa-solid fa-paste"
        title="Из"
        @click="action('copyFrom')"
      />
      <i
        v-tippy
        class="fa-solid fa-xmark clear"
        title="Очистить"
        @click="action('clear')"
      />
    </div>
    <VueTippyDiv
      :tag="props.tag"
      :text="props.text"
      :tippy-max-width="props.tippyMaxWidth"
      class="position-text"
    />
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

const emit = defineEmits(['copyTop', 'copyFrom', 'clear']);

const action = (emitType: string) => {
  emit(emitType, { employeePositionId: props.employeePositionId });
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
.clear {
  color: red;
}
</style>
