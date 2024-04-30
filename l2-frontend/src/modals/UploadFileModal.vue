<template>
  <div class="pointer">
    <slot @click.prevent="openModal">
      <a
      >{{ titleLocal }}
      </a>
    </slot>
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
        <div class="body">
          <UploadFile
            :types-file="props.typesFile"
            :forms-file="props.formsFile"
            :upload-result="props.uploadResult"
            :entity-id="props.entityId"
            :other-need-data="props.otherNeedData"
          />
        </div>
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
import {
  onMounted, PropType, ref,
} from 'vue';

import Modal from '@/ui-cards/Modal.vue';
import UploadFile from '@/components/UploadFile.vue';

const props = defineProps({
  title: {
    type: String,
    required: false,
  },
  typesFile: {
    type: Array as PropType<string[]>,
    required: false,
  },
  formsFile: {
    type: Array as PropType<string[]>,
    required: false,
  },
  uploadResult: {
    type: Boolean,
    required: false,
  },
  entityId: {
    type: Number,
    required: false,
  },
  otherNeedData: {
    type: Object || Array || String || Number,
    required: false,
  },
});
const titleLocal = ref('');
onMounted(() => {
  titleLocal.value = props.title ? props.title : 'Загрузка файла';
});
const open = ref(false);
const openModal = () => {
  open.value = true;
};
</script>

<style scoped lang="scss">
.pointer {
  cursor: pointer;
}
.body {
  height: 300px;
}
</style>
