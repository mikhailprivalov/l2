<template>
  <Longpress
    v-tippy
    :confirm-time="0"
    :duration="400"
    :on-confirm="onConfirm"
    :value="pk"
    action-text="×"
    class="btn btn-default btn-field"
    pressing-text="×"
    title="Очистить поле (удерживайте кнопку)"
  >
    ×
  </Longpress>
</template>

<script lang="ts">
// @ts-ignore
import Longpress from 'vue-longpress';

export default {
  name: 'LPress',
  components: { Longpress },
  props: {
    onConfirm: Function,
    pk: Number,
  },
};
</script>
