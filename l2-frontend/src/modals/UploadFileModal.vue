<template>
  <div class="pointer">
    <a
      @click.prevent="openModal"
    >{{ titleLocal }}
    </a>
    <Modal
      v-if="open"
      show-footer="true"
      ignore-body
      white-bg="true"
      max-width="710px"
      width="100%"
      margin-left-right="auto"
      @close="open = false"
    >
      <span slot="header">{{ titleLocal }}</span>
      <div slot="body">
        <UploadFile
          :types-file="props.typesFile"
          :forms-file="props.formsFile"
        />
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="open = false"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import Modal from '@/ui-cards/Modal.vue';
import UploadFile from '@/components/UploadFile.vue';

const props = defineProps({
  title: {
    type: String,
    required: false,
  },
  typesFile: {
    type: Array,
    required: false,
  },
  formsFile: {
    type: Array,
    required: false,
  },
  uploadResult: {
    type: Boolean,
    required: false,
  },
});

const titleLocal = computed(() => (props.title ? props.title : 'Загрузка файла'));

const open = ref(false);
const openModal = () => {
  open.value = true;
};
</script>

<style scoped lang="scss">
.pointer {
  cursor: pointer;
}
</style>
