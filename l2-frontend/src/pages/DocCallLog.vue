<template>
  <div>
    <div class="log-form">
      <div class="left">
        <textarea class="form-control" placeholder="Запись в журнале" v-model="text"></textarea>
      </div>
      <div class="right">
        <button class="btn btn-blue-nb btn-block" type="button" @click="createLog"
                :disabled="!text && status === -1 && !file">
          Сохранить
        </button>
        <select v-model="status" class="form-control" style="margin-top: 5px">
          <option :value="-1">Не обновлять статус</option>
          <option :value="1" v-if="r.status !== 1">Статус: Новая заявка</option>
          <option :value="2" v-if="r.status !== 2">Статус: В работе</option>
          <option :value="3" v-if="r.status !== 3">Статус: Выполнено</option>
          <option :value="4" v-if="r.status !== 4">Статус: Отмена</option>
        </select>
      </div>
    </div>
    <div class="log-file">
      <input type="file" ref="file" style="display: none"
             @change="fileChange($event.target.files)"/>
      <template v-if="!file">
        <a href="#" @click.prevent="$refs.file.click()" class="a-under-reversed">
          <i class="fa fa-folder"></i> добавить файл
        </a>
        (не более 5 МБ, не более 10 штук на одну заявку)
      </template>
      <template v-else>
        <a href="#" @click.prevent="file = ''; fileName = ''" class="a-under-reversed" title="Удалить файл" v-tippy>
          <i class="fa fa-file"></i>
          <span class="black">
            {{ fileName }} ({{ fileSize }} МБ)
          </span>
          &nbsp;&nbsp;<i class="fa fa-times"></i>
        </a>
      </template>
    </div>
    <div class="log-rows">
      <div v-if="rows.length === 0" class="log-row-empty">Нет записей</div>
      <div class="log-row" v-for="row in rows" :key="row.pk">
        <div class="log-row-author">{{ row.author }}</div>
        <div class="log-row-time">{{ row.createdAt }}</div>
        <div class="log-row-text" v-if="row.text">{{ row.text }}</div>
        <div class="log-row-system" v-if="row.executorFrom || row.executorTo">
          Изменение исполнителя:
          {{ row.executorFrom || 'нет' }} → <strong>{{ row.executorTo || 'нет' }}</strong>
        </div>
        <div class="log-row-system" v-if="row.statusFrom || row.statusTo">
          Изменение статуса:
          {{ row.statusFrom || 'нет' }} → <strong>{{ row.statusTo || 'нет' }}</strong>
        </div>
        <div class="log-row-system log-row-file" v-if="row.file">
          Прикреплённый файл:
          <a :href="row.file" target="_blank" class="a-under">
            {{ row.fileName }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as actions from '@/store/action-types';
import api from '@/api';
import axios from 'axios';

export default {
  name: 'DocCallLog',
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
      text: '',
      status: -1,
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
        window.errmessage('Файл больше 5 МБ');
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
        status: this.r.status,
        text: this.text,
        newStatus: this.status,
      });
      const blob = new Blob([json], {
        type: 'application/json',
      });

      const formData = new FormData();
      formData.append('file', this.file);
      formData.append('form', blob);

      const {
        data: {
          ok, message, status, executor, executor_fio, inLog,
        },
      } = await axios.post('/api/doctor-call/add-log',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

      if (!ok) {
        window.errmessage(message);
      } else {
        window.okmessage('Сохранено');
        this.status = -1;
        this.text = '';
        this.file = '';
        this.fileName = '';
        this.fileSize = '';
        this.$refs.file.value = '';
      }
      this.r.executor = executor;
      this.r.executor_fio = executor_fio;
      this.r.status = status;
      this.r.inLog = inLog;
      this.$root.$emit('doc-call:status:updated', this.r.pk);
      await this.$store.dispatch(actions.DEC_LOADING);
      await this.loadRows();
    },
    async loadRows() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { rows } = await api('doctor-call/log', this.r, 'pk');
      this.rows = rows;
      this.r.inLog = rows.length;
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.log-form {
  display: flex;

  .left, .right {
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
