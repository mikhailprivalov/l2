<template>
  <div v-frag>
    <a
      href="#"
      class="btn btn-blue-nb n-r"
      @click.prevent="show_modal"
    >
      Файлы
      <span class="badge badge-secondary">{{ count_files }}</span>
    </a>
    <FileAddModal
      v-if="showModal"
      :iss_pk="iss_pk"
    />
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
