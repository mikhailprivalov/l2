<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import useLoader from '@/hooks/useLoader';
import useOn from '@/hooks/useOn';
import usePrint from '@/hooks/usePrint';
import { menuItems } from '@/pages/CaseControl/Sidebar/menu';
import DisplayDirection from '@/pages/Stationar/DisplayDirection.vue';
import api from '@/api';
import ResultsViewer from '@/modals/ResultsViewer.vue';

// eslint-disable-next-line no-spaced-func,func-call-spacing
const emit = defineEmits<{
  (e: 'input', value: number): void
  (e: 'close-view'): void
  (e: 'close-direction'): void
}>();
const props = defineProps<{
  caseId?: number | null;
  view?: string | null;
  value?: number | null;
}>();

type Direction = {
  pk: number;
  confirm: boolean;
  date_create: boolean;
  researches_short: string[];
  researches: string[];
  showResults: boolean;
};

const loader = useLoader();
const { printResults } = usePrint();
const mainItem = computed(() => menuItems[props.view]);
const directions = ref<Direction[]>([]);
const showResultsId = ref<number | null>(null);

const loadDirections = async () => {
  if (!props.caseId || !props.view) {
    return;
  }
  loader.inc();
  const { rows } = await api('cases/directions-by-key', { caseId: props.caseId, view: props.view });
  directions.value = rows;
  loader.dec();
};

watch([() => props.view, () => props.caseId], loadDirections, {
  immediate: true,
});

useOn('result-saved', loadDirections);
useOn('researches-picker:directions_createdcase', loadDirections);

// eslint-disable-next-line @typescript-eslint/no-empty-function
const printAll = () => {
  printResults(directions.value.map((d) => d.pk));
};
const close = () => {
  emit('close-view');
};
const closeDirection = () => {
  emit('close-direction');
};
const openDirection = (d: Direction) => {
  if (d.showResults) {
    showResultsId.value = d.pk;
  } else if (props.view === 'all') {
    printResults([d.pk]);
  } else {
    emit('input', d.pk);
  }
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
        Boolean(d.confirm) && $style.confirmed,
        props.value === d.pk && $style.active,
        $style.block,
        $style.direction,
      ]"
      @click="openDirection(d)"
    >
      <span>
        <DisplayDirection :direction="d" />
        <i
          v-if="props.value === d.pk"
          class="fa fa-times"
          :class="$style.topRight"
          @click="closeDirection"
        />
      </span>
    </div>
    <ResultsViewer
      v-if="showResultsId"
      :pk="showResultsId"
      no_desc
      @hide="showResultsId = null"
    />
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

  &:hover:not(.active) {
    z-index: 1;
    transform: translateY(-1px);
  }

  &:not(.confirmed):not(.active):hover {
    box-shadow: 0 7px 14px rgba(0, 0, 0, 0.1), 0 5px 5px rgba(0, 0, 0, 0.12);
  }

  &.confirmed {
    border-color: #049372;
    background: linear-gradient(to bottom, #04937254 0%, #049372ba 100%);

    &:hover:not(.active) {
      box-shadow: 0 7px 14px #04937254, 0 5px 5px #049372ba;
    }
  }

  &.active {
    background-image: linear-gradient(#6c7a89, #56616c) !important;
    color: #fff !important;
  }
}
</style>
