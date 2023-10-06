<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import useLoader from '@/hooks/useLoader';
import { menuItems } from '@/pages/CaseControl/Sidebar/menu';
import DisplayDirection from '@/pages/Stationar/DisplayDirection.vue';
import api from '@/api';

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'open-direction', id: number): void
  (e: 'close-view', view: string): void
}>();
const props = defineProps<{
  caseId?: number | null;
  view?: string | null;
  selectedDirection?: number | null;
}>();

const loader = useLoader();
const mainItem = computed(() => menuItems[props.view]);
const directions = ref<any[]>([]);

watch([() => props.view, () => props.caseId], async () => {
  if (!props.caseId || !props.view) {
    return;
  }
  loader.inc();
  const { rows } = await api('cases/directions-by-key', { caseId: props.caseId, view: props.view });
  directions.value = rows;
  loader.dec();
}, {
  immediate: true,
});

// eslint-disable-next-line @typescript-eslint/no-empty-function
const printAll = () => {
};
const close = () => {
  emit('close-view');
};
const openDirection = (id: number) => {
  emit('open-direction', id);
};
</script>

<template>
  <div v-frag>
    <div :class="[$style.block, $style.title]">
      <span>
        {{ mainItem }}
        <br>
        <a
          href="#"
          class="a-under"
          @click.prevent="printAll"
        ><i class="fa fa-print" /> результатов</a>
      </span>
      <i
        class="fa fa-times"
        :class="$style.topRight"
        @click="close"
      />
    </div>
    <div
      v-for="d in directions"
      :key="d.pk"
      :class="[
        Boolean(d.totalConfirmed) && $style.confirmed,
        props.selectedDirection === d.pk && $style.active,
        $style.block,
        $style.direction,
      ]"
      @click="openDirection(d.pk)"
    >
      <span>
        <DisplayDirection :direction="d" />
      </span>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  name: 'TopView',
};
</script>

<style module lang="scss">
.block {
  display: inline-flex;
  align-items: center;
  justify-content: center;

  span {
    align-self: center;
    display: inline-block;
    text-align: center;
  }

  vertical-align: top;
  height: 100%;
  white-space: normal;
  width: 130px;
  padding: 3px;
  margin-right: 3px;
  border-radius: 3px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.01) 0%, rgba(0, 0, 0, 0.07) 100%);
}

.title {
  position: relative;
}

.topRight {
  position: absolute;
  top: 0;
  right: 0;
  padding: 3px;
  color: lightgray;
  cursor: pointer;

  &:hover {
    color: #000;
  }
}

.direction {
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;

  span {
    display: block;
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
  }

  &:hover {
    z-index: 1;
    transform: translateY(-1px);
  }

  &:not(.confirmed):hover {
    box-shadow: 0 7px 14px rgba(0, 0, 0, 0.1), 0 5px 5px rgba(0, 0, 0, 0.12);
  }

  &.confirmed {
    border-color: #049372;
    background: linear-gradient(to bottom, #04937254 0%, #049372ba 100%);

    &:hover {
      box-shadow: 0 7px 14px #04937254, 0 5px 5px #049372ba;
    }
  }

  &.active {
    background-image: linear-gradient(#6c7a89, #56616c) !important;
    color: #fff !important;
  }
}
</style>
