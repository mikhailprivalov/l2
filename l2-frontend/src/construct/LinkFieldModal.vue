<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    min-width="95%"
    margin-left-right="37px"
    @close="closeModal"
  >
    <span slot="header">Создание ссылочных строк</span>
    <div
      slot="body"
      class="body"
    >
      <VueTippyDiv
        class="link-text"
        :text="`Текущая ссылка - ${currentLinkString}`"
      />
      <LinkLabAdd
        :link-value="valueLink"
        :researches="researches"
        @add-lab-data="changeValueLink"
      />
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-6">
          <div>
            <div class="input-group">
              <span class="input-group-addon nbr">Где искать</span>
              <Treeselect
                v-model="hospType"
                :options="hospTypes"
                class="nbr"
                :clearable="false"
              />
              <span class="input-group-addon nbr">Сколько дней назад</span>
              <input
                v-model="daysAgo"
                class="form-control nbr days-ago"
                type="number"
                min="0"
              >
            </div>
          </div>
        </div>
        <div class="col-xs-2" />
        <div class="col-xs-2">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb nbr"
            @click="addLink"
          >
            Сохранить
          </button>
        </div>
        <div class="col-xs-2">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb nbr"
            @click="closeModal"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import {
  computed, onMounted, ref, watch,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';
import LinkLabAdd from '@/construct/LinkLabAdd.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import api from '@/api';
import { useStore } from '@/store';
import VueTippyDiv from '@/pages/ManageChambers/components/VueTippyDiv.vue';

const store = useStore();
const emit = defineEmits(['close-modal', 'add-link']);

const props = defineProps({
  fieldId: {
    required: true,
    type: Number,
  },
  fieldValue: {
    required: true,
    type: String,
  },
});

const hospTypes = ref([
  { id: '%root_hosp', label: 'Весь cлучай госпитализации' },
  { id: '%current_hosp', label: 'Текущее отделение' },
]);
const hospType = ref('%root_hosp');

const valueType = ref('laboratory');
const valueLink = ref('');
const daysAgo = ref(0);

watch(daysAgo, () => {
  if (daysAgo.value < 0) {
    daysAgo.value = 0;
  }
});

const researches = ref([]);
const getResearches = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('researches/researches-for-formula', { type: valueType.value });
  await store.dispatch(actions.DEC_LOADING);
  researches.value = result;
};

const currentLinkString = computed(() => {
  if (valueLink.value.length > 2) {
    return `${hospType.value}#${valueType.value}#${valueLink.value}#days_ago#${daysAgo.value}`;
  }
  return '';
});

const addLink = () => {
  emit('add-link', currentLinkString.value);
};
const closeModal = () => {
  emit('close-modal');
};

const changeValueLink = (value) => {
  valueLink.value = value;
};

const parseCurrentFieldValue = () => {
  const { fieldValue } = props;
  if (!fieldValue || (fieldValue && fieldValue.trim().length === 0)) {
    return;
  }
  const [typeHosp, typeValue, value, , countDaysAgo]: [string, string, string, string] = fieldValue.split('#');
  if (!typeHosp || !typeValue || !value) {
    return;
  }
  const normalizeTypeHosp = typeHosp.trim();
  let normalizeDaysAgo = '0';
  if (countDaysAgo) {
    normalizeDaysAgo = countDaysAgo.trim();
  }
  const normalizeTypeValue = typeValue.trim();
  const normalyzeValue = value.trim();
  hospType.value = normalizeTypeHosp;
  const numberDaysAgo = Number(normalizeDaysAgo);
  daysAgo.value = numberDaysAgo || 0;
  valueType.value = normalizeTypeValue;
  valueLink.value = normalyzeValue;
};

onMounted(async () => {
  await getResearches();
  parseCurrentFieldValue();
});
</script>

<style scoped lang="scss">
.body {
  height: 100%;
  width: 100%;
  padding: 10px 15px;
}
.flex {
  display: flex;
}
.save-button {
  padding: 7px 5px;
}
.type-hosp {
  width: 300px;
}
.type-hosp-label {
  width: 100px;
}
.days-ago {
  width: 105px;
}
.gap5 {
  gap: 5px;
}
::v-deep .nbr .vue-treeselect__control {
  border-radius: 0;
}
.link-text {
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}
</style>
