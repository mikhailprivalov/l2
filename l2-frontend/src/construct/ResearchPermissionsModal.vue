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
            :options="users"
          />
        </div>
      </div>
      <div class="save-button">
        <button class="btn btn-blue-nb nbr">
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
import { ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

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

const hide = () => {
  emit('hide');
};

const selectedDepartment = ref(null);

const selectedUsers = ref(null);
const users = ref([]);
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
