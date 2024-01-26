<template>
  <Modal
    ref="modal"
    margin-top="30px"
    margin-left-right="auto"
    max-width="1000px"
    height="560px"
    show-footer="true"
    width="100%"
    @close="hideModal"
  >
    <span slot="header">Настройка анализа ({{ 'ff' }}) </span>
    <div
      slot="body"
      class="root"
    >
      <label>Памятка</label>
      <textarea
        v-model="instruction"
        class="form-control"
        rows="4"
      />
      <label>Варианты комментариев</label>
      <Treeselect
        v-model="selectVariant"
        :options="variants"
      />
      <label>Шаблон формы</label>
      <Treeselect
        v-model="selectTemplate"
        :options="templatesForm"
      />
      <button
        class="btn btn-blue-nb"
        @click="update"
      >
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

import {
  getCurrentInstance, onMounted, ref,
} from 'vue';
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import api from '@/api';
import { useStore } from '@/store';

const props = defineProps({
  researchId: {
    type: Number,
    required: true,
  },
});
const emit = defineEmits(['hideAdditionalModal']);
const store = useStore();
const root = getCurrentInstance().proxy.$root;

const modal = ref(null);
const hideModal = () => {
  emit('hideAdditionalModal');
  if (modal.value) {
    modal.value.$el.style.display = 'none';
  }
};

const researchAdditionalData = ref({});
const selectVariant = ref(null);
const variants = ref([]);
const selectTemplate = ref(null);
const instruction = ref(null);

const templatesForm = ref([
  { id: 0, label: '0' },
  { id: 1, label: '1' },
  { id: 2, label: '2' },
  { id: 3, label: '3' },
  { id: 4, label: '4' },
]);

const getAdditionalData = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-research-additional-data', { researchPk: props.researchId });
  await store.dispatch(actions.DEC_LOADING);
  researchAdditionalData.value = result;
};

const getCommentVariants = async () => {
  await store.dispatch(actions.INC_LOADING);
  const { result } = await api('construct/laboratory/get-comments-variants');
  await store.dispatch(actions.DEC_LOADING);
  variants.value = result;
};

const update = async () => {
  root.$emit('msg', 'ok', 'Сохранено');
};

onMounted(() => {
  getCommentVariants();
  getAdditionalData();
});

</script>

<style scoped lang="scss">
.root {
  height: 439px;
}
</style>
