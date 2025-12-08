<template>
  <div class="position">
    <div class="top-icons">
      <i
        ref="lunch"
        v-tippy="{
          html: `#tempLunch${props.employeePositionId}`,
          arrow: true,
          reactive: true,
          interactive: true,
          animation: 'fade',
          duration: 0,
          theme: 'light',
          placement: 'bottom',
          trigger: 'click',
        }"
        class="fa-solid fa-cutlery icon-color"
      />
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
      :id="`tempLunch${props.employeePositionId}`"
      class="tp-lunch"
    >
      <div class="lunch-settings">
        <label for="withLunch">{{ withLunch ? 'С обедом' : 'Без обеда' }}</label>
        <input
          id="withLunch"
          v-model="withLunch"
          type="checkbox"
        >
        <br>
        <RadioFieldById
          v-if="withLunch"
          v-model="selectedLunchDurationInMinutes"
          :variants="lunchDurations"
          class="lunch-duration-variants"
          :start-null="true"
        />
        <button
          class="btn btn-blue-nb"
          :disabled="withLunch && !selectedLunchDurationInMinutes"
          @click="editLunch"
        >
          Сохранить
        </button>
      </div>
    </div>
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
      >
        <label
          slot="option-label"
          slot-scope="{ node }"
          v-tippy="{
            maxWidth: '50%'
          }"
          class="treeselect-options"
          :title="node.label"
        > {{ node.label }}</label>
      </Treeselect>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref, watch } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import VueTippyDiv from '@/pages/ManageChambers/components/VueTippyDiv.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import RadioFieldById from '@/fields/RadioFieldById.vue';

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
  employeeLunchDuration: {
    type: [Number, undefined, null],
    required: false,
  },
  employeePositions: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(['copyTop', 'copyFrom', 'clear', 'editLunch']);
const root = getCurrentInstance().proxy.$root;
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
  label: `${node.fio} (${node.bidType})`,
});
const clear = () => {
  emit('clear', { rowIndex: props.rowIndex });
};

const lunch = ref(null);
const withLunch = ref(false);
const selectedLunchDurationInMinutes = ref(null);
const lunchDurations = ref([
  { id: 30, label: '30' },
  { id: 60, label: '60' },
  { id: 90, label: '90' },
  { id: 120, label: '120' },
]);
watch(withLunch, () => {
  if (!withLunch.value && selectedLunchDurationInMinutes.value) {
    selectedLunchDurationInMinutes.value = null;
  }
});
const editLunch = () => {
  if (withLunch.value && !selectedLunchDurationInMinutes.value) {
    root.$emit('msg', 'error', 'Значение обеда не выбрано');
  } else {
    const lunchDurationInMinutes = withLunch.value ? selectedLunchDurationInMinutes.value : 0;
    emit('editLunch', {
      employeePositionId: props.employeePositionId,
      lunchDurationInMinutes,
    });
  }
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
.tp-lunch {
  height: auto;
  width: 300px;
}
.icon-color {
  color: #636e7e;
}
.treeselect-options {
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  margin-bottom: 0;
  padding-top: 6px;
}
.lunch-duration-variants {
  height: 19px;
  margin-bottom: 5px;
}
.lunch-settings {
  text-align: left;
}
</style>
