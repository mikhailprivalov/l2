<template>
  <div class="position">
    <div class="top-icons">
      <i
        v-tippy
        class="fa-solid fa-copy"
        title="Сверху"
        @click="copy('copyTop')"
      />
      <i
        v-tippy
        class="fa-solid fa-paste"
        title="Из"
        @click="copy('copyFrom')"
      />
      <i
        v-tippy
        class="fa-solid fa-xmark clear"
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
  rowIndex: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits(['copyTop', 'copyFrom', 'clear']);

const copy = (copyType: string) => {
  if (props.rowIndex !== 0) {
    emit(copyType, { rowIndex: props.rowIndex });
  }
};
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
.clear {
  color: red;
}
</style>
