<template>
  <div>
    <div class="log-form">
      <div class="left">
        <textarea
          v-model="text"
          class="form-control"
          placeholder="Запись в журнале"
        />
      </div>
      <div class="right">
        <button
          class="btn btn-blue-nb btn-block"
          type="button"
          :disabled="!text && status === -1 && !file"
          @click="createLog"
        >
          Сохранить
        </button>
        <select
          v-model="status"
          class="form-control"
          style="margin-top: 5px"
        >
          <option :value="-1">
            Не обновлять статус
          </option>
          <option
            v-if="r.status !== 1"
            :value="1"
          >
            Статус: Новая заявка
          </option>
          <option
            v-if="r.status !== 2"
            :value="2"
          >
            Статус: В работе
          </option>
          <option
            v-if="r.status !== 3"
            :value="3"
          >
            Статус: Выполнено
          </option>
          <option
            v-if="r.status !== 4"
            :value="4"
          >
            Статус: Отмена
          </option>
        </select>
      </div>
    </div>
    <div class="log-file">
      <input
        ref="file"
        type="file"
        style="display: none"
        @change="fileChange($event.target.files)"
      >
      <template v-if="!file">
        <a
          href="#"
          class="a-under-reversed"
          @click.prevent="$refs.file.click()"
        > <i class="fa fa-folder" /> добавить файл </a>
        (не более 5 МБ, не более 10 штук на одну заявку)
      </template>
      <template v-else>
        <a
          v-tippy
          href="#"
          class="a-under-reversed"
          title="Удалить файл"
          @click.prevent="
            file = '';
            fileName = '';
          "
        >
          <i class="fa fa-file" />
          <span class="black"> {{ fileName }} ({{ fileSize }} МБ) </span>
          &nbsp;&nbsp;<i class="fa fa-times" />
        </a>
      </template>
    </div>
    <div class="log-rows">
      <div
        v-if="rows.length === 0"
        class="log-row-empty"
      >
        Нет записей
      </div>
      <div
        v-for="row in rows"
        :key="row.pk"
        class="log-row"
      >
        <div class="log-row-author">
          {{ row.author }}
        </div>
        <div class="log-row-time">
          {{ row.createdAt }}
        </div>
        <div
          v-if="row.text"
          class="log-row-text"
        >
          {{ row.text }}
        </div>
        <div
          v-if="row.executorFrom || row.executorTo"
          class="log-row-system"
        >
          Изменение исполнителя:
          {{ row.executorFrom || 'нет' }} → <strong>{{ row.executorTo || 'нет' }}</strong>
        </div>
        <div
          v-if="row.statusFrom || row.statusTo"
          class="log-row-system"
        >
          Изменение статуса:
          {{ row.statusFrom || 'нет' }} → <strong>{{ row.statusTo || 'нет' }}</strong>
        </div>
        <div
          v-if="row.file"
          class="log-row-system log-row-file"
        >
          Прикреплённый файл:
          <a
            :href="row.file"
            target="_blank"
            class="a-under"
          >
            {{ row.fileName }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import axios from 'axios';
import * as Cookies from 'es-cookie';

import * as actions from '@/store/action-types';

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
          ok, message, status, executor, executor_fio: executorFio, inLog,
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
        this.text = '';
        this.file = '';
        this.fileName = '';
        this.fileSize = '';
        this.$refs.file.value = '';
      }
      // eslint-disable-next-line vue/no-mutating-props
      this.r.executor = executor;
      // eslint-disable-next-line vue/no-mutating-props
      this.r.executor_fio = executorFio;
      // eslint-disable-next-line vue/no-mutating-props
      this.r.status = status;
      // eslint-disable-next-line vue/no-mutating-props
      this.r.inLog = inLog;
      this.$root.$emit('doc-call:status:updated', this.r.pk);
      await this.$store.dispatch(actions.DEC_LOADING);
      await this.loadRows();
    },
    async loadRows() {
      await this.$store.dispatch(actions.INC_LOADING);
      const { rows } = await this.$api('doctor-call/log', this.r, 'pk');
      this.rows = rows;
      // eslint-disable-next-line vue/no-mutating-props
      this.r.inLog = rows.length;
      await this.$store.dispatch(actions.DEC_LOADING);
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
