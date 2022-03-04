<template>
  <div v-frag>
    <a href="#" @click.prevent="show_modal" class="btn btn-blue-nb n-r">Файлы-{{count_files}}</a>
    <file-add-modal v-if="showModal" :iss_pk="iss_pk"/>
  </div>
</template>

<script lang="ts">
import FileAddModal from '@/modals/FileAddModal.vue';

export default {
  name: 'FileAdd',
  components: { FileAddModal },
  props: {
    iss_pk: {
      type: Number,
      required: false,
    },
    count_files: {
      type: Number,
      required: false,
    },
  },
  data() {
    return {
      showModal: false,
    };
  },
  mounted() {
    this.$root.$on('file-add:modal:hide', () => {
      this.showModal = false;
    });
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
