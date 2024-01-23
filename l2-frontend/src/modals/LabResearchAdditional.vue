<template>
  <Modal
    ref="modal"
    margin-top="30px"
    margin-left-right="auto"
    max-width="1500px"
    height="360px"
    show-footer="true"
    white-bg="true"
    width="100%"
    @close="hideModal"
  >
    <span slot="header">Настройка анализа ({{ 'ff' }}) </span>
    <div
      slot="body"
    >
      <label>Памятка</label>
      <textarea
        class="form-control"
        rows="4"
      />
      <label>Варианты комментариев</label>
      <Treeselect />
      <label>Шаблон формы</label>
      <Treeselect />
      <button class="btn btn-blue-nb">
        Сохранить
      </button>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-10" />
        <div class="col-xs-2">
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
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

import { ref } from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';

import '@riophae/vue-treeselect/dist/vue-treeselect.css';

// const props = defineProps({
//   editRelationId: {
//     type: Number,
//     required: true,
//   },
// });
const emit = defineEmits(['hideAdditionalModal']);
const modal = ref(null);
const hideModal = () => {
  emit('hideAdditionalModal');
  if (modal.value) {
    modal.value.$el.style.display = 'none';
  }
};
</script>
