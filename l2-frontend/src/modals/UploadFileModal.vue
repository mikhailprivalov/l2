<template>
  <div>
    <a
      @click.prevent="openModal">{{ titleLocal }}
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
        <UploadFile />
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-4">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              :disabled="loading"
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
import { ref, computed } from 'vue'

import Modal from "@/ui-cards/Modal.vue";
import UploadFile from "@/components/UploadFile.vue";
import Component from "vue-class-component";

const props = defineProps({
  title: {
    type: String,
    required: false,
  }
})

const titleLocal = computed(() => {
  return props.title ? props.title : 'Загрузка файла'
})

const open = ref(false);
const openModal = () => {
  open.value = true;
}
</script>

<style scoped lang="scss">

</style>
