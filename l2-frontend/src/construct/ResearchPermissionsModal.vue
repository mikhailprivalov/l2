<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    margin-top
    margin-left-right="auto"
    @close="hide"
  >
    <span slot="header">Доступ к настройке услуги</span>
    <div
      slot="body"
      class="body"
    >
      <div class="flex margin-bottom">
        <div class="right-border">
          <label>Подразделения</label>
          <Treeselect
            v-model="selectedDepartment"
            class="treeselect-noborder"
            placeholder="Выберите подразделение..."
            :options="props.departments"
          />
        </div>
        <div>
          <label>Пользователи</label>
          <Treeselect
            v-model="selectedUsers"
            class="treeselect-noborder"
            placeholder="Выберите пользователей..."
            :multiple="true"
            :disable-branch-nodes="true"
            :options="usersData"
          />
        </div>
      </div>
      <div class="save-button">
        <button
          class="btn btn-blue-nb nbr"
          @click="save"
        >
          Сохранить
        </button>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-8" />
        <div class="col-xs-4">
          <button
            type="button"
            class="btn btn-primary-nb btn-blue-nb"
            @click="hide"
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
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';
import { useStore } from '@/store';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import api from '@/api';

const store = useStore();
const emit = defineEmits(['hide']);
const props = defineProps({
  researchId: {
    type: Number,
    required: true,
  },
  departments: {
    type: Array,
    required: true,
  },
});

const root = getCurrentInstance().proxy.$root;

const hide = () => {
  emit('hide');
};

const selectedDepartment = ref(null);

const selectedUsers = ref(null);
const usersData = ref([]);
const getUsers = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { users } = await api('load-users-by-group', { group: '*' });
  await store.dispatch(actions.DEC_LOADING);
  usersData.value = users;
};
onMounted(async () => {
  await getUsers();
});

const getPermissions = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { departmentId, userIds } = await api('researches/get-research-permissions', { researchId: props.researchId });
  await store.dispatch(actions.DEC_LOADING);
  console.log(departmentId);
  console.log(userIds);
  selectedDepartment.value = departmentId;
  selectedUsers.value = userIds;
};
onMounted(async () => {
  await getPermissions();
});
const save = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { ok, message } = await api('researches/save-research-permissions', {
    researchId: props.researchId,
    userIds: selectedUsers.value,
    departmentId: selectedDepartment.value,
  });
  await store.dispatch(actions.DEC_LOADING);
  if (ok) {
    root.$emit('msg', 'ok', 'Сохранено');
    await getPermissions();
  } else {
    root.$emit('msg', 'error', message);
  }
};
</script>

<style scoped lang="scss">
.body {
  width: 800px;
  min-height: 200px;
  padding: 0 5px;
}
.flex {
  display: flex;
}
.margin-bottom {
  margin-bottom: 20px;
}
.save-button {
  float: right;
}
.right-border {
  border-right: 1px solid #ddd;
}
</style>
