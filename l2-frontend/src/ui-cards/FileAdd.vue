<template>
  <div v-frag>
    <a href="`http://ya.ru`" @click.prevent="show_modal" class="btn btn-blue-nb n-r">Файлы</a>
    <file-add-modal v-if="showModal"/>
  </div>
</template>

<script lang="ts">
import FileAddModal from '@/modals/FileAddModal.vue';

export default {
  name: 'FileAdd',
  components: { FileAddModal },
  props: {
    med_certificates: {
      type: Array,
      required: false,
    },
    direction: {
      type: Number,
      required: false,
    },
  },
  data() {
    return {
      showModal: false,
    };
  },
  methods: {
    show_modal() {
      this.showModal = true;
    },
  },
};
</script>

<style scoped lang="scss">
.n-r {
  border-radius: 0;
}
</style>
