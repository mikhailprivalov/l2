<template>
  <div v-frag>
    <component
      :is="tag"
      v-show="Boolean(l2_load_file || l2_csv_load_file || l2_equipment_load_file)"
    >
      <a
        href="#"
        :class="isLoadGroupForProtocol && 'btn btn-blue-nb'"
        @click.prevent="doOpen"
      >
        {{ titleButton }}
      </a>
      <Modal
        v-if="open"
        show-footer="true"
        ignore-body
        white-bg="true"
        max-width="710px"
        width="100%"
        margin-left-right="auto"
        @close="open = false"
      >
        <span slot="header">{{ titleButton }}</span>
        <div slot="body">
          <template v-if="l2_equipment_load_file">
            <div class="form-group">
              <div
                class="input-group"
                style="width: 100%"
              >
                <span class="input-group-addon">Оборудование</span>
                <Treeselect
                  v-model="equipment"
                  class="treeselect-nbr treeselect-wide treeselect-34px"
                  :multiple="false"
                  :disable-branch-nodes="true"
                  :options="equipments"
                  placeholder="Оборудование не указано"
                  :append-to-body="true"
                  :clearable="false"
                  :z-index="10000"
                />
              </div>
              <input
                id="fileInput"
                ref="equipmentFile"
                style="margin-top: 15px"
                type="file"
                class="form-control-file"
                :readonly="loading"
                :accept="fileFilter"
                @change="handleEquipmentFileUpload()"
              >
            </div>
            <button
              style="width: 200px;"
              type="button"
              class="btn btn-primary"
              :disabled="!Boolean(equipmentFile) || loading"
              @click="submitEquipment()"
            >
              <i
                v-if="loading"
                class="fa fa-spinner"
              />
              <span v-else>Загрузить</span>
            </button>
          </template>
          <template v-else-if="l2_load_file">
            <div class="form-group">
              <label for="fileInput"> {{ company === true || fileFilter === 'XLSX'?
                'XLSX файл' : (isLoadGroupForProtocol ? 'JSON': 'PDF') }}</label>
              <input
                id="fileInput"
                ref="file"
                type="file"
                class="form-control-file"
                :readonly="loading"
                :accept="fileFilter"
                @change="handleFileUpload()"
              >
              <div
                v-if="isLoadResultService"
                class="input-group"
                style="width: 100%; margin-top: 10px"
              >
                <span class="input-group-addon">Id услуги</span>
                <input
                  v-model="idService"
                  class="form-control"
                >
                <span class="input-group-addon">Id врача</span>
                <input
                  v-model="idDoctorProfile"
                  class="form-control"
                >
                <span class="input-group-addon">Источник финансирования</span>
                <input
                  v-model="financingSourceTitle"
                  class="form-control"
                >
              </div>
              <div
                v-if="isLoadResultService"
                class="input-group"
                style="width: 100%; margin-top: 5px"
              >
                <span class="input-group-addon">Названия полей</span>
                <input
                  v-model="titleFields"
                  class="form-control"
                  placeholder="fio, lastname, firstname, patronymic, sex, birthday, address, snils, enp, Диагноз, Дата осмотра..."
                >
              </div>
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
              <span v-else>Загрузить {{ company === true || fileFilter === 'XLSX' ?
                'XLSX' : (isLoadGroupForProtocol ? 'JSON': 'PDF') }}</span>
            </button>
          </template>
          <template v-if="l2_csv_load_file">
            <div class="form-group">
              <label for="fileInput">CSV файл</label>
              <input
                id="fileInput"
                ref="csvFile"
                type="file"
                class="form-control-file"
                :readonly="loading"
                :accept="fileFilter"
                @change="handleCsvFileUpload()"
              >
            </div>
            <button
              style="width: 200px;"
              type="button"
              class="btn btn-primary"
              :disabled="!Boolean(csvFile) || loading"
              @click="submitCSV()"
            >
              <i
                v-if="loading"
                class="fa fa-spinner"
              />
              <span v-else>Загрузить CSV</span>
            </button>
          </template>
          <h5 v-if="results.length > 0">
            {{ company === true ? 'Не сохраненные результаты': 'Сохранённые результаты' }}
          </h5>
          <ul v-if="results.length !== 0 && !link && !company">
            <li v-if="method">
              Методика: {{ method }}
            </li>
            <li
              v-for="r in results"
              :key="r.pk"
            >
              {{ r.pk }} – {{ r.result }} <small v-if="r.comment">{{ r.comment }}</small>
            </li>
          </ul>
          <ul v-if="company">
            <li
              v-for="r in results"
              :key="r.pk"
            >
              {{ r.fio }} - {{ r.reason }}
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
    </component>
  </div>
</template>

<script lang="ts">
import axios from 'axios';
import * as Cookies from 'es-cookie';
import Treeselect from '@riophae/vue-treeselect';

import Modal from '@/ui-cards/Modal.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

export default {
  name: 'LoadFile',
  components: { Modal, Treeselect },
  props: {
    tag: {
      type: String,
      default: 'li',
    },
    companyInn: {
      type: String,
      default: '',
      required: false,
    },
    fileFilter: {
      type: String,
      default: null,
      required: false,
    },
    classess: {
      type: String,
      default: '',
    },
    isGenCommercialOffer: {
      type: Boolean,
      default: false,
      required: false,
    },
    isWritePatientEcp: {
      type: Boolean,
      default: false,
      required: false,
    },
    isLoadResultService: {
      type: Boolean,
      default: false,
      required: false,
    },
    isLoadGroupForProtocol: {
      type: Boolean,
      default: false,
      required: false,
    },
    researchId: {
      type: Number,
      default: -1,
      required: false,
    },
    selectedPrice: {
      type: Number,
      default: -1,
      required: false,
    },
    titleButton: {
      type: String,
      default: 'Загрузка файла',
      required: false,
    },
    researchSet: {
      type: Number,
      default: -1,
      required: false,
    },
  },
  data() {
    return {
      open: false,
      loading: false,
      file: '',
      csvFile: '',
      equipmentFile: '',
      method: null,
      results: [],
      company: false,
      link: null,
      contentLoadGroupForProtocol: null,
      idService: null,
      idDoctorProfile: null,
      financingSourceTitle: null,
      titleFields: null,
      equipments: [],
      equipment: null,
    };
  },
  computed: {
    l2_load_file() {
      return this.$store.getters.modules.l2_load_file;
    },
    l2_csv_load_file() {
      return this.$store.getters.modules.l2_csv_load_file;
    },
    l2_equipment_load_file() {
      return this.$store.getters.modules.l2_equipment_load_file;
    },
  },
  methods: {
    doOpen() {
      this.file = '';
      this.open = true;
      this.results = [];
      this.method = null;
      this.company = false;
      this.link = null;
      this.getEquipments();
    },
    handleFileUpload() {
      // eslint-disable-next-line prefer-destructuring
      this.file = this.$refs.file.files[0];
      if (this.isLoadGroupForProtocol) {
        const reader = new FileReader();
        reader.onload = (res) => {
          this.contentLoadGroupForProtocol = res.target.result;
        };
        reader.readAsText(this.file);
      }
    },
    handleCsvFileUpload() {
      // eslint-disable-next-line prefer-destructuring
      this.csvFile = this.$refs.csvFile.files[0];
    },
    handleEquipmentFileUpload() {
      // eslint-disable-next-line prefer-destructuring
      this.equipmentFile = this.$refs.equipmentFile.files[0];
    },
    async submit() {
      this.loading = true;
      try {
        this.results = [];
        const formData = new FormData();
        formData.append('file', this.file);
        formData.append('companyInn', this.companyInn);
        formData.append('isGenCommercialOffer', this.isGenCommercialOffer);
        formData.append('selectedPrice', this.selectedPrice);
        formData.append('isWritePatientEcp', this.isWritePatientEcp);
        formData.append('isLoadResultService', this.isLoadResultService);
        formData.append('isLoadGroupForProtocol', this.isLoadGroupForProtocol);
        formData.append('researchId', this.researchId);
        formData.append('researchSet', this.researchSet);
        formData.append('idService', this.idService);
        formData.append('idDoctorProfile', this.idDoctorProfile);
        formData.append('financingSourceTitle', this.financingSourceTitle);
        formData.append('titleFields', this.titleFields);
        if (this.isLoadGroupForProtocol) {
          this.$emit('load-file', this.contentLoadGroupForProtocol);
          this.open = false;
          this.loading = false;
        } else {
          const { data } = await axios.post('/api/parse-file/loadfile', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
              'X-CSRFToken': Cookies.get('csrftoken'),
            },
          });
          this.results = data.results;
          this.method = null;
          this.company = data.company;
          this.$refs.file.value = '';
          this.file = '';
          this.$root.$emit('msg', 'ok', 'Файл загружен');
          this.link = data.link;
          if (this.link) {
            window.open(`/statistic/${this.link}?file=${encodeURIComponent(JSON.stringify(data.results))}`, '_blank');
          }
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.$root.$emit('msg', 'error', 'Ошибка');
      }
      this.loading = false;
    },
    async submitCSV() {
      this.loading = true;
      try {
        this.results = [];
        const formData = new FormData();
        formData.append('file', this.csvFile);
        formData.append('selectedPrice', this.selectedPrice);
        const { data } = await axios.post('/api/parse-file/loadcsv', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'X-CSRFToken': Cookies.get('csrftoken'),
          },
        });
        if (Object.hasOwn(data, 'ok') && !data.ok) {
          this.$root.$emit('msg', 'error', data.message || 'Ошибка');
          this.loading = false;
          return;
        }
        this.results = data.results;
        this.method = data.method || null;
        this.$refs.csvFile.value = '';
        this.csvFile = '';
        this.$root.$emit('msg', 'ok', 'Файл загружен');
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.$root.$emit('msg', 'error', 'Ошибка');
      }
      this.loading = false;
    },
    async submitEquipment() {
      this.loading = true;
      try {
        this.results = [];
        const formData = new FormData();
        formData.append('file', this.equipmentFile);
        formData.append('equipment', this.equipment);
        const { data } = await axios.post('/api/parse-file/loadequipment', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'X-CSRFToken': Cookies.get('csrftoken'),
          },
        });
        if (Object.hasOwn(data, 'ok') && !data.ok) {
          this.$root.$emit('msg', 'error', data.message || 'Ошибка');
          this.loading = false;
          return;
        }
        this.results = data.results;
        this.method = data.method || null;
        this.$refs.equipmentFile.value = '';
        this.equipmentFile = '';
        this.$root.$emit('msg', 'ok', 'Файл загружен');
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
        this.$root.$emit('msg', 'error', 'Ошибка');
      }
      this.loading = false;
    },
    async getEquipments() {
      const formData = new FormData();
      formData.append('companyInn', this.equipment);
      const list = await this.$api('analyzers/analyzers-load-file');
      this.equipments = list.data;
    },
  },
};
</script>

<style lang="scss" scoped>
.btn + .form-group {
  margin-top: 10px;
}
</style>
