<template>
  <div class="object-owner">
    <div class="object-owner__header">
      <span>Владелец</span>
      <button
        class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
        type="button"
        title="Добавить"
        @click="openCreateModal"
      >
        <i class="fa fa-plus" />
      </button>
    </div>
    <div
      v-if="!currentOwner"
      class="object-owner__empty"
    >
      <span>Нет данных о владельце</span>
      <button
        v-if="owners.length > 0"
        class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
        type="button"
        title="История"
        @click="openHistoryModal"
      >
        <i class="fa fa-history" />
      </button>
    </div>
    <div
      v-else
      class="object-owner__body"
    >
      <table class="object-owner__table">
        <thead>
          <tr>
            <th>Начало</th>
            <th>Окончание</th>
            <th>ФИО</th>
            <th>Д/р</th>
            <th>Тел.</th>
            <th class="object-owner__col-actions" />
          </tr>
        </thead>
        <tbody>
          <tr :key="currentOwner.owner_id">
            <td>{{ formatDate(currentOwner.date_start) }}</td>
            <td>{{ formatDate(currentOwner.date_end) }}</td>
            <td :title="formatFio(currentOwner)">
              {{ formatFio(currentOwner) }}
            </td>
            <td>{{ formatDate(currentOwner.birthday) }}</td>
            <td :title="formatPhones(currentOwner)">
              {{ formatPhones(currentOwner) }}
            </td>
            <td class="object-owner__col-actions">
              <button
                class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                type="button"
                title="История"
                :disabled="owners.length === 0"
                @click="openHistoryModal"
              >
                <i class="fa fa-history" />
              </button>
              <button
                class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                type="button"
                title="Редактировать"
                @click="openEditModal(currentOwner)"
              >
                <i class="fa fa-pencil" />
              </button>
              <button
                class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                type="button"
                title="Удалить"
                @click="deleteOwner(currentOwner)"
              >
                <i class="fa fa-minus" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <MountingPortal
      mount-to="#portal-place-modal"
      name="GardeningObjectOwnerHistoryModal"
      append
    >
      <transition name="fade">
        <Modal
          v-if="historyModalOpen"
          show-footer="true"
          white-bg="true"
          max-width="860px"
          width="100%"
          margin-left-right="auto"
          @close="closeHistoryModal"
        >
          <span slot="header">История владельцев</span>
          <div
            slot="body"
            class="history-modal-body"
          >
            <div
              v-if="owners.length === 0"
              class="object-owner__empty"
            >
              Нет данных о владельце
            </div>
            <table
              v-else
              class="object-owner__table"
            >
              <thead>
                <tr>
                  <th>Начало</th>
                  <th>Окончание</th>
                  <th>ФИО</th>
                  <th>Д/р</th>
                  <th>Тел.</th>
                  <th class="object-owner__col-actions" />
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in owners"
                  :key="item.owner_id"
                >
                  <td>{{ formatDate(item.date_start) }}</td>
                  <td>{{ formatDate(item.date_end) }}</td>
                  <td :title="formatFio(item)">
                    {{ formatFio(item) }}
                  </td>
                  <td>{{ formatDate(item.birthday) }}</td>
                  <td :title="formatPhones(item)">
                    {{ formatPhones(item) }}
                  </td>
                  <td class="object-owner__col-actions object-owner__col-actions--history">
                    <button
                      class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                      type="button"
                      title="Редактировать"
                      @click="openEditModal(item)"
                    >
                      <i class="fa fa-pencil" />
                    </button>
                    <button
                      class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                      type="button"
                      title="Удалить"
                      @click="deleteOwner(item)"
                    >
                      <i class="fa fa-minus" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-9" />
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  @click="closeHistoryModal"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>

    <MountingPortal
      mount-to="#portal-place-modal"
      name="GardeningObjectOwnerModal"
      append
    >
      <transition name="fade">
        <Modal
          v-if="modalOpen"
          show-footer="true"
          white-bg="true"
          max-width="520px"
          width="100%"
          margin-left-right="auto"
          @close="closeModal"
        >
          <span slot="header">{{ editingOwnerId ? 'Редактировать владельца' : 'Добавить владельца' }}</span>
          <div
            slot="body"
            class="modal-body-form"
          >
            <div class="form-group">
              <label>Дата начала</label>
              <input
                v-model="formDateStart"
                class="form-control"
                type="date"
              >
            </div>
            <div class="form-group">
              <label>Дата окончания</label>
              <input
                v-model="formDateEnd"
                class="form-control"
                type="date"
              >
            </div>
            <div class="form-group">
              <label>Фамилия</label>
              <input
                v-model.trim="formFamily"
                class="form-control"
                type="text"
              >
            </div>
            <div class="form-group">
              <label>Имя</label>
              <input
                v-model.trim="formName"
                class="form-control"
                type="text"
              >
            </div>
            <div class="form-group">
              <label>Отчество</label>
              <input
                v-model.trim="formPatronymic"
                class="form-control"
                type="text"
              >
            </div>
            <div class="form-group">
              <label>Дата рождения</label>
              <input
                v-model="formBirthday"
                class="form-control"
                type="date"
              >
            </div>
            <div class="form-group">
              <div class="phones-header">
                <label>Телефоны</label>
                <button
                  class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                  type="button"
                  title="Добавить телефон"
                  @click="addPhoneRow"
                >
                  <i class="fa fa-plus" />
                </button>
              </div>
              <div
                v-if="formPhones.length === 0"
                class="phones-empty"
              >
                Нет телефонов
              </div>
              <div
                v-for="(phone, index) in formPhones"
                :key="`phone-${index}`"
                class="phone-row"
              >
                <input
                  v-model="formPhones[index]"
                  v-mask="'8(999)999-99-99'"
                  class="form-control"
                  type="text"
                  placeholder="8(999)999-99-99"
                >
                <button
                  class="btn btn-blue-nb btn-sm nbr toolbar-icon-btn"
                  type="button"
                  title="Удалить"
                  @click="removePhoneRow(index)"
                >
                  <i class="fa fa-times" />
                </button>
              </div>
            </div>
          </div>
          <div slot="footer">
            <div class="row">
              <div class="col-xs-6" />
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  :disabled="saving || !canSave"
                  @click="saveOwner"
                >
                  Сохранить
                </button>
              </div>
              <div class="col-xs-3">
                <button
                  class="btn btn-primary-nb btn-blue-nb"
                  type="button"
                  :disabled="saving"
                  @click="closeModal"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </Modal>
      </transition>
    </MountingPortal>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  ref,
  watch,
} from 'vue';

import { useStore } from '@/store';
import * as actions from '@/store/action-types';
import api from '@/api';
import Modal from '@/ui-cards/Modal.vue';

interface OwnerPhone {
  id?: number;
  phone: string;
}

interface OwnerInfo {
  owner_id: number;
  individual_id: number | null;
  family: string;
  name: string;
  patronymic: string;
  birthday: string | null;
  date_start: string | null;
  date_end: string | null;
  phones?: OwnerPhone[];
}

const props = defineProps<{
  realEstateId: number;
}>();

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const owners = ref<OwnerInfo[]>([]);
const modalOpen = ref(false);
const historyModalOpen = ref(false);
const saving = ref(false);
const editingOwnerId = ref<number | null>(null);
const formDateStart = ref('');
const formDateEnd = ref('');
const formFamily = ref('');
const formName = ref('');
const formPatronymic = ref('');
const formBirthday = ref('');
const formPhones = ref<string[]>([]);

const currentOwner = computed(() => {
  const openOwners = owners.value.filter((item) => !item.date_end);
  if (openOwners.length === 0) {
    return null;
  }
  return openOwners.reduce((latest, item) => {
    if (!latest.date_start) {
      return item;
    }
    if (!item.date_start) {
      return latest;
    }
    return item.date_start > latest.date_start ? item : latest;
  });
});

const canSave = computed(() => (
  Boolean(formDateStart.value)
  && Boolean(formBirthday.value)
  && Boolean(formFamily.value || formName.value || formPatronymic.value)
));

const formatDate = (value: string | null) => {
  if (!value) {
    return '—';
  }
  const [year, month, day] = value.split('-');
  if (!year || !month || !day) {
    return value;
  }
  return `${day}.${month}.${year}`;
};

const formatFio = (item: OwnerInfo) => {
  const parts = [item.family, item.name, item.patronymic]
    .map((part) => (part || '').trim())
    .filter(Boolean);
  return parts.length > 0 ? parts.join(' ') : '—';
};

const formatPhones = (item: OwnerInfo) => {
  const first = (item.phones || []).map((row) => row.phone).find(Boolean);
  return first || '—';
};

const addPhoneRow = () => {
  formPhones.value.push('');
};

const removePhoneRow = (index: number) => {
  formPhones.value.splice(index, 1);
};

const resetForm = () => {
  editingOwnerId.value = null;
  formDateStart.value = '';
  formDateEnd.value = '';
  formFamily.value = '';
  formName.value = '';
  formPatronymic.value = '';
  formBirthday.value = '';
  formPhones.value = [''];
};

const fillForm = (item: OwnerInfo) => {
  editingOwnerId.value = item.owner_id;
  formDateStart.value = item.date_start || '';
  formDateEnd.value = item.date_end || '';
  formFamily.value = item.family || '';
  formName.value = item.name || '';
  formPatronymic.value = item.patronymic || '';
  formBirthday.value = item.birthday || '';
  const phones = (item.phones || []).map((row) => row.phone).filter(Boolean);
  formPhones.value = phones.length > 0 ? [...phones] : [''];
};

const loadOwners = async () => {
  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/get-real-estate-owner', {
      real_estate_id: props.realEstateId,
    });
    if (ok === false) {
      root.$emit('msg', 'error', message || 'Не удалось загрузить владельца');
      owners.value = [];
      return;
    }
    owners.value = Array.isArray(result) ? result : [];
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

const openCreateModal = () => {
  resetForm();
  modalOpen.value = true;
};

const openEditModal = (item: OwnerInfo) => {
  fillForm(item);
  modalOpen.value = true;
};

const closeModal = () => {
  modalOpen.value = false;
};

const openHistoryModal = () => {
  historyModalOpen.value = true;
};

const closeHistoryModal = () => {
  historyModalOpen.value = false;
};

const saveOwner = async () => {
  if (saving.value || !canSave.value) {
    return;
  }
  saving.value = true;
  await store.dispatch(actions.INC_LOADING);
  try {
    const payload: Record<string, unknown> = {
      real_estate_id: props.realEstateId,
      family: formFamily.value,
      name: formName.value,
      patronymic: formPatronymic.value,
      birthday: formBirthday.value,
      date_start: formDateStart.value,
      date_end: formDateEnd.value || null,
      phones: formPhones.value,
    };
    if (editingOwnerId.value) {
      payload.owner_id = editingOwnerId.value;
    }
    const { ok, message, result } = await api('gardening/save-real-estate-owner', payload);
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось сохранить');
      return;
    }
    root.$emit('msg', 'ok', 'Сохранено');
    owners.value = Array.isArray(result) ? result : [];
    closeModal();
  } finally {
    saving.value = false;
    await store.dispatch(actions.DEC_LOADING);
  }
};

const deleteOwner = async (item: OwnerInfo) => {
  try {
    await root.$dialog.confirm('Удалить владельца?');
  } catch (_) {
    return;
  }

  await store.dispatch(actions.INC_LOADING);
  try {
    const { ok, message, result } = await api('gardening/delete-real-estate-owner', {
      owner_id: item.owner_id,
    });
    if (!ok) {
      root.$emit('msg', 'error', message || 'Не удалось удалить');
      return;
    }
    root.$emit('msg', 'ok', 'Удалено');
    owners.value = Array.isArray(result) ? result : [];
    if (editingOwnerId.value === item.owner_id) {
      closeModal();
    }
  } finally {
    await store.dispatch(actions.DEC_LOADING);
  }
};

watch(() => props.realEstateId, () => {
  loadOwners();
}, { immediate: true });
</script>

<style scoped lang="scss">
.object-owner {
  display: flex;
  flex-direction: column;
  width: 50%;
  max-width: 50%;
  height: 100%;
  min-height: 0;
  background-color: #f8f7f7;
  border-bottom: none;
}

.object-owner__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  box-sizing: border-box;
  height: 34px;
  min-height: 34px;
  padding: 0 10px;
  border-bottom: 1px solid #b1b1b1;
  color: #FFFFFF;
  font-weight: bold;
  background-color: #aab2bd;
  flex-shrink: 0;
}

.toolbar-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 22px;
  min-height: 22px;
  max-height: 22px;
  min-width: 22px;
  padding: 0 6px;
  flex-shrink: 0;
  line-height: 1;
  box-sizing: border-box;
}

.object-owner__empty {
  display: flex;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  padding: 10px;
  color: #666;
}

.history-modal-body {
  max-height: 60vh;
  overflow: auto;
}

.object-owner__body {
  overflow: auto;
  min-height: 0;
}

.object-owner__table {
  width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  color: #434A54;

  th,
  td {
    box-sizing: border-box;
    height: 34px;
    padding: 0 6px;
    border-bottom: 1px solid #b1b1b1;
    text-align: left;
    vertical-align: middle;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  th {
    font-weight: bold;
    background-color: #ececec;
  }

  th:nth-child(1),
  td:nth-child(1),
  th:nth-child(2),
  td:nth-child(2),
  th:nth-child(4),
  td:nth-child(4) {
    width: 95px;
  }

  th:nth-child(3),
  td:nth-child(3) {
    width: 28%;
  }

  th:nth-child(5),
  td:nth-child(5) {
    width: auto;
  }

  th:nth-child(6),
  td:nth-child(6),
  th.object-owner__col-actions,
  td.object-owner__col-actions {
    width: 108px;
    min-width: 108px;
    padding-left: 2px;
    padding-right: 2px;
    text-align: center;
    overflow: visible;
    text-overflow: clip;
  }

  td.object-owner__col-actions--history {
    width: 76px;
    min-width: 76px;
  }

  .object-owner__col-actions .toolbar-icon-btn {
    margin: 0 1px;
    vertical-align: middle;
  }
}

.modal-body-form {
  padding: 10px 0;
}

.modal-body-form .form-group {
  margin-bottom: 12px;
}

.modal-body-form label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
}

.phones-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;

  label {
    margin-bottom: 0;
  }
}

.phones-empty {
  color: #666;
  margin-bottom: 6px;
}

.phone-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
