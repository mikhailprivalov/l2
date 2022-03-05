<template>
  <modal
    ref="modal"
    @close="hide"
    show-footer="true"
    white-bg="true"
    max-width="600px"
    width="100%"
    height="20%"
    marginLeftRight="auto"
    margin-top
    class="an"
  >
    <span slot="header">Управление файлами</span>
    <div slot="body">
      <div class="rows-file">
        <input type="file" ref="file" style="display: none" @change="fileChange($event.target.files)"/>
        <div v-if="!file">
          <h6>
            <a href="#" @click.prevent="$refs.file.click()" class="a-under-reversed"> <i class="fa fa-folder"></i>
              Загрузить файл
            </a>
            (max- 5 шт. по 5 МБ)
          </h6>
        </div>
        <div v-else>
          <a
            href="#"
            @click.prevent="
            file = '';
            fileName = '';
          "
            class="a-under-reversed"
            title="Удалить файл"
            v-tippy
          >
            <i class="fa fa-file"></i>
            <span class="black"> {{ fileName }} ({{ fileSize }} МБ) </span>
            &nbsp;&nbsp;<i class="fa fa-times"></i>
          </a>
        </div>
        <div v-if="rows.length === 0">Нет записей</div>
        <div v-for="(row, index) in rows" :key="row.pk">
          <br/>
           <a :href="row.file" target="_blank" class="rows-file" >{{ index + 1 }} - {{ row.fileName }}</a>
        </div>
     </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-5" style="float: right">
          <button @click="hide" class="btn btn-primary-nb btn-blue-nb" type="button">
            Закрыть
          </button>
        </div>
        <div class="col-xs-5" style="float: right">
          <button class="btn btn-blue-nb btn-block" type="button" @click="addFile" :disabled="!file">
            Сохранить
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script lang="ts">
import axios from 'axios';
import * as Cookies from 'es-cookie';
import * as actions from '@/store/action-types';
import Modal from '@/ui-cards/Modal.vue';

export default {
  name: 'FileAddModal',
  components: { Modal },
  props: {
    iss_pk: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      file: '',
      fileName: '',
      fileSize: '',
      rows: [],
    };
  },
  mounted() {
    this.loadRows();
  },
  methods: {
    fileChange(fileList) {
      const [file] = fileList;
      if (!file) {
        this.file = '';
        this.fileName = '';
        this.fileSize = '';
        return;
      }
      const size = Number(file.size);
      if (size > 5242880) {
        this.$root.$emit('msg', 'error', 'Файл больше 5 МБ');
        return;
      }
      this.file = file;
      this.fileName = file.name;
      this.fileSize = Math.round((size / 1024 / 1024) * 100) / 100;
    },
    async addFile() {
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
        data: {
          ok, message,
        },
      } = await axios.post('/api/directions/add-file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-CSRFToken': Cookies.get('csrftoken'),
        },
      });

      if (!ok) {
        this.$root.$emit('msg', 'error', message);
      } else {
        this.$root.$emit('msg', 'ok', 'Сохранено');
        this.status = -1;
        this.file = '';
        this.fileName = '';
        this.fileSize = '';
        this.$refs.file.value = '';
      }
      await this.$store.dispatch(actions.DEC_LOADING);
      await this.loadRows();
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
.rows-file {
  float: left;
  padding-left: 30px;
}

</style>
