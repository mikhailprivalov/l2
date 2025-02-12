<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    min-width="95%"
    @close="closeModal"
  >
    <span slot="header">Создание ссылочных строк</span>
    <div
      slot="body"
      class="body"
    >
      <LinkLabAdd
        :value="valueLink"
        @add-link="addLink"
      />
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-10">
          <div>
            <div class="flex gap5 margin">
              <div class="type-hosp">
                <label>Где искать</label>
                <Treeselect
                  v-model="hospType"
                  :options="hospTypes"
                  class="nbr"
                  :clearable="false"
                />
              </div>
              <div class="days-ago">
                <label>Кол-во дн. назад</label>
                <input
                  v-model="daysAgo"
                  class="form-control nbr"
                  type="number"
                >
              </div>
            </div>
            <div class="margin">
              <button
                class="btn btn-blue-nb save-button nbr"
                @click="addLink"
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
        <div class="col-xs-2">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
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
import { onMounted, ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';
import LinkLabAdd from '@/construct/LinkLabAdd.vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

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
  { id: '%current_hosp', label: 'Текущая история' },
]);
const hospType = ref('%root_hosp');

const valueType = ref('laboratory');
const valueLink = ref('');
const daysAgo = ref(0);

const closeModal = () => {
  emit('close-modal');
};

const currentLinkData = ref('');

const addLink = ({ currentLinkString }) => {
  currentLinkData.value = `${hospType.value}#laboratory#${currentLinkString}#days_ago${daysAgo.value}`;
  emit('add-link', currentLinkData.value);
};

const parseCurrentFieldValue = () => {
  const { fieldValue } = props;
  if (!fieldValue || (fieldValue && fieldValue.trim().length === 0)) {
    return;
  }
  const [typeHosp, typeValue, value, countDaysAgo]: [string, string, string, string] = fieldValue.split('#');
  if (!typeHosp || !typeValue || !value) {
    return;
  }
  const normalizeDaysAgo = countDaysAgo.trim();
  const normalizeTypeValue = typeValue.trim();
  const normalyzeValue = value.trim();
  daysAgo.value = Number(normalizeDaysAgo);
  valueType.value = normalizeTypeValue;
  valueLink.value = normalyzeValue;
};

onMounted(() => {
  parseCurrentFieldValue();
});
</script>

<style scoped lang="scss">
.body {
  height: 100%;
  width: 100%;
}
.flex {
  display: flex;
}
.margin {
  margin: 5px;
}
.margin {
  margin: 5px;
}
.save-button {
  padding: 7px 5px;
}
.type-hosp {
  width: 300px;
}
.days-ago {
  width: 125px;
}
.gap5 {
  gap: 5px;
}
::v-deep .nbr .vue-treeselect__control {
  border-radius: 0;
}
</style>
