<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="50%"
    min-width="800px"
    width="50%"
    margin-left-right="auto"
    margin-top="48px"
    @close="hideModal"
  >
    <span slot="header">Перенос услуги в другую карту</span>
    <div
      slot="body"
      style="min-height: 340px"
    >
      <h6><strong>Пациент: </strong>{{ patientFio }}</h6>
      <div
        id="row-box"
        class="row"
      >
        <div class="col-xs-6">
          <h6><strong>Изменить принадлежность:</strong></h6>
          <ul>
            <li
              v-for="dir in directions_checked"
              :key="dir.pk"
            >
              <span><strong>{{ dir.pk }}</strong>- {{ dir.researches }}</span>
            </li>
          </ul>
        </div>
        <div
          id="box-right"
          class="col-xs-6"
        >
          <h6><strong>Номер карты:</strong></h6>
          <input
            v-model.trim="newCardNumber"
            class="form-control"
            placeholder="Введите номер карты"
          >
        </div>
      </div>
    </div>

    <div slot="footer">
      <div class="row">
        <div class="col-xs-4">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            :disabled="!newCardNumber"
            @click="moveDirectionToCard"
          >
            Сохранить
          </button>
        </div>
        <div class="col-xs-4">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            @click="hideModal"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { getCurrentInstance, onMounted, ref } from 'vue';

import Modal from '@/ui-cards/Modal.vue';
import * as actions from '@/store/action-types';
import patientsPoint from '@/api/patients-point';
import directionsPoint from '@/api/directions-point';

const api = getCurrentInstance().proxy.$api;
const root = getCurrentInstance().proxy.$root;
const refs = getCurrentInstance().proxy.$refs;
const store = getCurrentInstance().proxy.$store;
const dialog = getCurrentInstance().proxy.$dialog;

const patientFio = ref('');
const oldCardNumber = ref('');
const newCardNumber = ref('');

const props = defineProps({
  card_pk: {
    type: Number,
    default: -1,
    required: false,
  },
  directions_checked: {
    type: Array,
    required: true,
  },
  kk: {
    type: String,
    default: '',
  },
});

const hideModal = () => {
  root.$emit('hide_move_direction');
  if (refs.modal) {
    refs.modal.$el.style.display = 'none';
  }
  root.$emit('update_card_data');
  root.$emit(`researches-picker:refresh${props.kk}`);
};

const loadData = async () => {
  await store.dispatch(actions.INC_LOADING);
  await patientsPoint.searchL2Card({ card_pk: props.card_pk }).then(({ results: [data] }) => {
    patientFio.value = `${data.family} ${data.name} ${data.twoname}`;
    oldCardNumber.value = data.num;
  });
  await store.dispatch(actions.DEC_LOADING);
};

const moveDirectionToCard = async () => {
  const { ok, individual_fio: individualFio } = await api('patients/is-card', {
    number: newCardNumber.value,
  });
  if (!ok) {
    root.$emit('msg', 'error', 'Карта не найдена');
    return;
  }
  try {
    await dialog.confirm(
      `Перенести услугу из карты №${oldCardNumber.value} — ${patientFio.value}
       в карту №${newCardNumber.value} — ${individualFio} ?`,
    );
  } catch (e) {
    return;
  }
  await store.dispatch(actions.INC_LOADING);
  const directionNumber = props.directions_checked[0].pk;
  const data = await api('directions/change-owner-direction', {
    old_card_number: oldCardNumber.value,
    new_card_number: newCardNumber.value,
    direction_number: directionNumber,
  });
  await directionsPoint.updateParent({ parent: -1, slave_dirs: [directionNumber] });
  root.$emit('msg', 'ok', 'Направление успешно перенесено');
  root.$emit('msg', 'ok', `Номер: ${data.directions}`);
  hideModal();
  await store.dispatch(actions.DEC_LOADING);
};

onMounted(() => {
  loadData();
});
</script>

<style scoped lang="scss">
.invalid {
  color: #d35400;
  cursor: pointer;
}

.isDisabled {
  cursor: not-allowed;
  opacity: 0.7;
  color: #d35400;
}

#row-box {
  display: flex;
}

#box-right {
  border-left: 1px solid silver;
}

ul {
  font-size: 13px;
  padding: 0;
}

li {
  list-style-type: none;
  padding: 5px;
}
</style>
