<template>
  <component
    :is="props.tag"
  >
    <slot>
      <a
        class="pointer"
        @click.prevent="openModal"
      >{{ titleLocal }}
      </a>
    </slot>
    <transition name="fade">
      <ShiftModal
        v-if="showModal"
        @closeModal="closeModal"
      />
    </transition>
  </component>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import ShiftModal from '@/ui-cards/CashRegisters/ShiftModal.vue';
import { useStore } from '@/store';

const store = useStore();
const props = defineProps({
  tag: {
    type: String,
    default: 'li',
    required: false,
  },
});

const cashRegister = computed(() => store.getters.cashRegisterShift);
const shiftIsOpen = computed(() => !!cashRegister.value?.cashRegisterId);

const titleLocal = computed(() => (shiftIsOpen.value ? 'Смена открыта' : 'Смена закрыта'));
const showModal = ref(false);

const openModal = () => {
  showModal.value = true;
};
const closeModal = () => {
  showModal.value = false;
};
</script>

<style scoped lang="scss">

</style>
