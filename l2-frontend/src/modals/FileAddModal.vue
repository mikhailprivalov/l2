<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="600px"
    width="100%"
    height="20%"
    margin-left-right="auto"
    margin-top
    class="an"
    @close="hide"
  >
    <span slot="header">Управление файлами</span>
    <div
      slot="body"
      class="modal-body"
    >
      <div
        v-if="rows.length < maxCountFiles"
        class="uploading-block"
      >
        <a
          href="#"
          :class="file ? 'a-under-reversed s-black' : 'a-under'"
          @click.prevent="changeFile"
        >
          <i class="fa fa-folder" />
          <template v-if="file">{{ fileName }}</template>
          <template v-else>выбрать файл (не более 5 МБ)</template>
        </a>

        <a
          v-if="file"
          v-tippy
          href="#"
          class="a-under ml-5"
          title="Отменить выбор"
          @click.prevent="file = ''"
        >
          <i class="fa fa-times" />
        </a>
      </div>
      <div v-if="file">
        <button
          class="btn btn-blue-nb btn-block btn-sm mt-5"
          type="button"
          @click="addFile"
        >
          <template v-if="uploading">
            <i class="fa fa-spinner" /> отправляем файл...
          </template>
          <template v-else>
            <i class="fa fa-upload" /> Прикрепить файл ({{ fileSize }})
          </template>
        </button>
      </div>
      <div
        v-if="rows.length === 0"
        class="empty"
      >
        Нет записей
      </div>
      <template v-else>
        <hr class="hrr">
        <ol class="file-list">
          <li
            v-for="row in rows"
            :key="row.pk"
          >
            <a
              :href="row.file"
              target="_blank"
              class="rows-file a-under"
            >{{ row.fileName }}</a>
          </li>
        </ol>
      </template>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-8" />
        <div class="col-xs-4">
          <button
            class="btn btn-primary-nb btn-blue-nb"
            type="button"
            @click="hide"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script lang="ts">
import axios from 'axios';
import * as Cookies from 'es-cookie';

import * as actions from '@/store/action-types';
import { selectFile } from '@/utils';
import Modal from '@/ui-cards/Modal.vue';

export default {
  name: 'FileAddModal',
  components: { Modal },
  props: {
    iss_pk: {
      type: Number,
      required: true,
    },
    maxCountFiles: {
      type: Number,
      required: false,
      default: 5,
    },
  },
  data() {
    return {
      file: '',
      fileName: '',
      fileSize: '',
      rows: [],
      uploading: false,
    };
  },
  mounted() {
    this.loadRows();
  },
  methods: {
    async changeFile() {
      const file = await selectFile(null);
      if (!file) {
        this.file = '';
        this.fileName = '';
        this.fileSize = '';
        return;
      }
      let size = Number(file.size);
      if (size > 5242880) {
        this.$root.$emit('msg', 'error', 'Файл больше 5 МБ');
        return;
      }
      this.file = file;
      this.fileName = file.name;
      size /= 1024;
      let mode = 'КБ';
      if (size >= 512) {
        size /= 1024;
        mode = 'МБ';
      }
      this.fileSize = `${Math.round(size * 100) / 100} ${mode}`;
    },
    async addFile() {
      this.uploading = true;
      await this.$store.dispatch(actions.INC_LOADING);

      const json = JSON.stringify({
        pk: this.iss_pk,
      });
      const blob = new Blob([json], {
        type: 'application/json',
      });

      const formData = new FormData();
      formData.append('file', this.file);
      formData.append('form', blob);

      const {
        data: { ok, message },
      } = await axios.post('/api/directions/add-file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-CSRFToken': Cookies.get('csrftoken'),
        },
      });
      if (ok) {
        await this.loadRows();
      }
      await this.$store.dispatch(actions.DEC_LOADING);
      this.uploading = false;
      if (!ok) {
        this.$root.$emit('msg', 'error', message);
      } else {
        this.$root.$emit('msg', 'ok', 'Сохранено');
        this.file = '';
        this.fileName = '';
        this.fileSize = '';
        this.$emit('add-file');
      }
    },
    async loadRows() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { rows } = await this.$api('directions/file-log', { pk: this.iss_pk });
      this.rows = rows;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    hide() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('file-add:modal:hide');
    },
  },
};
</script>

<style scoped lang="scss">
.s-black {
  color: black;
}

.modal-body {
  padding: 10px 15px;
}

.empty {
  margin: 15px 0 15px 0;
  padding: 10px;
  background-color: rgba(0, 0, 0, 8%);
  border-radius: 4px;
}

.uploading-block {
  margin-top: 10px;
}

.mt-5 {
  margin-top: 5px;
}

.ml-5 {
  margin-left: 5px;
  display: inline-block;
}

.file-list {
  padding-left: 18px;
}

.hrr {
  margin: 5px 0;
}
</style>
