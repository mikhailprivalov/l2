<template>
  <div v-frag>
    <button
      v-tippy
      class="btn btn-blue-nb file-btn"
      title="Просмотр и добавление файлов"
      @click="show_modal"
    >
      Файлы
      <span class="badge badge-secondary">{{ countFiles }}</span>
    </button>
    <MountingPortal
      mount-to="#portal-place-modal"
      :name="`FileAdd_${iss_pk}`"
      append
    >
      <FileAddModal
        v-if="showModal"
        :iss_pk="iss_pk"
        :max-count-files="maxCountFiles"
        @add-file="onAddFile"
      />
    </MountingPortal>
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
      default: 0,
    },
    maxCountFiles: {
      type: Number,
      required: false,
      default: 5,
    },
  },
  data() {
    return {
      showModal: false,
      countFilesAdd: 0,
    };
  },
  computed: {
    countFiles() {
      return this.countFilesAdd + this.count_files;
    },
  },
  mounted() {
    this.$root.$on('file-add:modal:hide', () => {
      this.showModal = false;
    });
  },
  methods: {
    onAddFile(total) {
      if (typeof total === 'number') {
        this.countFilesAdd = Math.max(0, total - this.count_files);
        return;
      }
      this.countFilesAdd += 1;
    },
    show_modal() {
      this.showModal = true;
    },
  },
};
</script>

<style scoped lang="scss">
.badge-secondary {
  background: rgb(129, 129, 129);
}
</style>
