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
    <div slot="body" class="an-body">
      <div class="log-file">
        <input type="file" ref="file" style="display: none" @change="fileChange($event.target.files)"/>
        <template v-if="!file">
          <h6>
          <a href="#" @click.prevent="$refs.file.click()" class="a-under-reversed"> <i class="fa fa-folder"></i>
            Загрузить файл
          </a>
          (max- 5 шт. по 5 МБ)
          </h6>
        </template>
        <template v-else>
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
        </template>
      </div>
<!--      <div class="log-rows">-->
<!--        <div v-if="rows.length === 0" class="log-row-empty">Нет записей</div>-->
<!--        <div class="log-row" v-for="row in rows" :key="row.pk">-->
<!--          <div class="log-row-author">{{ row.author }}</div>-->
<!--          <div class="log-row-system log-row-file" v-if="row.file">-->
<!--            Прикреплённый файл:-->
<!--            <a :href="row.file" target="_blank" class="a-under">-->
<!--              {{ row.fileName }}-->
<!--            </a>-->
<!--          </div>-->
<!--        </div>-->
<!--      </div>-->
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-5" style="float: right">
          <button @click="hide" class="btn btn-primary-nb btn-blue-nb" type="button">
            Закрыть
          </button>
        </div>
        <div class="col-xs-5" style="float: right">
          <button class="btn btn-blue-nb btn-block" type="button" @click="createLog" :disabled="!file">
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
    r: {
      type: Object,
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
    this.$root.$on('doc-call:log:update', () => this.loadRows());
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
    async createLog() {
      await this.$store.dispatch(actions.INC_LOADING);

      const json = JSON.stringify({
        pk: this.r.pk,
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
      } = await axios.post('/api/doctor-call/add-log', formData, {
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
      this.$root.$emit('doc-call:status:updated', this.r.pk);
      await this.$store.dispatch(actions.DEC_LOADING);
      await this.loadRows();
    },
    async loadRows() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { rows } = await this.$api('doctor-call/log', this.r, 'pk');
      this.rows = rows;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    hide() {
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('doc-call:row:modal:hide');
    },
  },
};
</script>

<style scoped lang="scss">
.log-form {
  display: flex;

  .left,
  .right {
    display: inline-block;
    height: 73px;
  }

  .left {
    width: calc(100% - 200px);
    padding-right: 5px;
  }

  .right {
    width: 200px;
  }

  textarea {
    width: 100%;
    height: 100%;
    resize: none;
  }
}

.log-row {
  padding: 5px;
  position: relative;
  background-color: #f7f1e4;
  border-radius: 5px;
  color: #5e5149;

  &s {
    margin-top: 10px;
  }

  &-empty {
    text-align: center;
    padding: 50px;
    color: gray;
  }

  &-author {
    font-weight: bold;
  }

  &-time {
    position: absolute;
    top: 3px;
    right: 5px;
  }

  &-text {
    white-space: pre-wrap;
    word-break: keep-all;
    padding: 3px;
    border-radius: 5px;
    border: 1px solid #eadcbd;
    background-color: #fbfbfb;
  }

  &-system {
    padding: 2px;
    margin-left: 2px;
    margin-top: 5px;
    border-left: 3px solid #decda3;
  }

  &-file a {
    color: #5e5149 !important;
  }

  & + & {
    margin-top: 10px;
  }
}

.log-file {
  margin-top: 3px;
  margin-left: 3px;
  font-size: 90%;

  a {
    .fa {
      margin-right: 3px;
    }

    .black {
      color: #000;
    }
  }
}
</style>
