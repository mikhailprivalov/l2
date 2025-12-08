<template>
  <div class="position">
    <div class="top-icons">
      <i
        ref="vacation"
        v-tippy="{
          html: `#tempVacation${props.employeePositionId}`,
          arrow: true,
          reactive: true,
          interactive: true,
          animation: 'fade',
          duration: 0,
          theme: 'light',
          placement: 'bottom',
          trigger: 'click',
        }"
        class="fa-solid icon-color"
      >О</i>
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
      :id="`tempVacation${props.employeePositionId}`"
      class="tp"
    >
      <div>
        <RadioFieldById
          v-model="selectedVacationFillMode"
          :variants="vacationFillMode"
          class="radio-select-variants"
        />
        <label class="tp-label">Начало</label>
        <input
          v-model="vacationStart"
          class="form-control"
          type="date"
          :min="props.firstDayMonth"
          :max="props.lastDayMonth"
        >
        <input
          v-if="selectedVacationFillMode === 'day'"
          v-model="vacationDurationInDays"
          class="form-control"
          type="number"
          min="0"
          max="31"
          :disabled="!vacationStart"
        >
        <input
          v-else
          v-model="vacationEnd"
          class="form-control"
          type="date"
          :disabled="!vacationStart"
          :min="props.firstDayMonth"
          :max="props.lastDayMonth"
        >
        <button
          class="btn btn-blue-nb"
          @click="fillVacation"
        >
          Сохранить
        </button>
      </div>
    </div>
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
          class="radio-select-variants"
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
import moment from 'moment';

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
  firstDayMonth: {
    type: String,
    required: true,
  },
  lastDayMonth: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['copyTop', 'copyFrom', 'clear', 'editLunch', 'fillVacation']);
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

const vacation = ref(null);
const vacationFillMode = ref([
  { id: 'day', label: 'Дни' },
  { id: 'date', label: 'Конец' },
]);
const selectedVacationFillMode = ref('day');
const vacationStart = ref(null);
const vacationDurationInDays = ref(0);
const vacationEnd = ref(null);

watch(vacationDurationInDays, () => {
  if (Number(vacationDurationInDays.value) < 0) {
    vacationDurationInDays.value = 0;
  } else if (!vacationStart.value) {
    root.$emit('msg', 'error', 'Дата начала не заполнена');
  } else {
    const lastMonthDay = moment(props.lastDayMonth);
    const vacationStartDate = moment(vacationStart.value);
    const vacationEndDate = moment(vacationStartDate).add(Number(vacationDurationInDays.value), 'days').subtract(1, 'day');
    if (vacationEndDate <= lastMonthDay) {
      vacationEnd.value = vacationEndDate.format('YYYY-MM-DD');
    } else {
      vacationEnd.value = lastMonthDay.format('YYYY-MM-DD');
    }
  }
});
const fillVacation = () => {
  emit('fillVacation', {
    employeePositionId: props.employeePositionId,
    vacationStart: vacationStart.value,
    vacationEnd: vacationEnd.value,
  });
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
.radio-select-variants {
  height: 19px;
  margin-bottom: 5px;
}
.lunch-settings {
  text-align: left;
}
</style>
