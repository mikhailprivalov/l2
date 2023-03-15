<template>
  <div v-frag>
    <li v-show="Boolean(l2_load_file)">
      <a
        href="#"
        @click.prevent="doOpen"
      >
        Загрузка файла
      </a>
      <Modal
        v-if="open"
        show-footer="true"
        white-bg="true"
        max-width="710px"
        width="100%"
        margin-left-right="auto"
        @close="open = false"
      >
        <span slot="header">Загрузка файла</span>
        <div slot="body">
          <div class="form-group">
            <label for="fileInput">PDF/XLSX файл</label>
            <input
              id="fileInput"
              ref="file"
              type="file"
              class="form-control-file"
              :readonly="loading"
              @change="handleFileUpload()"
            >
          </div>
          <button
            style="width: 200px;"
            type="button"
            class="btn btn-primary"
            :disabled="!Boolean(file) || loading"
            @click="submit()"
          >
            <i
              v-if="loading"
              class="fa fa-spinner"
            />
            <span v-else>Загрузить</span>
          </button>
          <h5 v-if="results.length > 0">
            Сохранённые результаты
          </h5>
          <ul>
            <li
              v-for="r in results"
              :key="r.pk"
            >
              {{ r.pk }} – {{ r.result }}
            </li>
          </ul>
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
    </li>
  </div>
</template>

<script lang="ts">
import axios from 'axios';
import * as Cookies from 'es-cookie';

import Modal from '@/ui-cards/Modal.vue';

export default {
  name: 'LoadFile',
  components: { Modal },
  props: {
    companyInn: {
      type: String,
      required: false,
    },
  },
  data() {
    return {
      open: false,
      loading: false,
      file: '',
      results: [],
    };
  },
  computed: {
    l2_load_file() {
      return this.$store.getters.modules.l2_load_file;
    },
  },
  methods: {
    doOpen() {
      this.file = '';
      this.open = true;
      this.results = [];
    },
    handleFileUpload() {
      // eslint-disable-next-line prefer-destructuring
      this.file = this.$refs.file.files[0];
    },
    async submit() {
      this.loading = true;
      try {
        this.results = [];
        const formData = new FormData();
        formData.append('file', this.file);
        formData.append('companyInn', this.companyInn);
        const { data } = await axios.post('/api/parse-file/loadfile', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'X-CSRFToken': Cookies.get('csrftoken'),
          },
        });
        this.results = data.results;
        this.$refs.file.value = '';
        this.file = '';
        this.$root.$emit('msg', 'ok', 'Файл загружен');
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.$root.$emit('msg', 'error', 'Ошибка');
      }
      this.loading = false;
    },
  },
};
</script>

<style lang="scss" scoped></style>
