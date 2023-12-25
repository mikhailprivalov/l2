<template>
  <div>
    <h5>
      <a
        class="a-under a-align"
        href="#"
        @click.prevent="downloadHarmFullFactors"
      >
        Скачать - Факторы вредности
      </a>
    </h5>

    <div>
      <input
        v-model.trim="search"
        class="form-control search"
        placeholder="Поиск"
      >
    </div>
    <div
      class="card-no-hover card card-1"
    >
      <div class="scroll">
        <table class="table">
          <colgroup>
            <col width="150">
            <col>
            <col width="285">
            <col width="200">
            <col width="99">
          </colgroup>
          <thead class="sticky">
            <tr>
              <th
                class="text-center"
              >
                <strong>Название</strong>
              </th>
              <th
                class="text-center"
              >
                <strong>Описание</strong>
              </th>
              <th class="text-center">
                <strong>UUID</strong>
              </th>
              <th
                class="text-center"
              >
                <strong>Шаблон</strong>
              </th>
              <th />
            </tr>
          </thead>
          <tr
            v-if="filteredFactors.length === 0"
            class="text-center"
          >
            <td
              colspan="4"
            >
              Нет данных
            </td>
          </tr>
          <tr
            v-for="(factor) in filteredFactors"
            :key="factor.id"
            class="table-row"
          >
            <td class="table-row">
              <RegexFormatInput
                v-model="factor.title"
                :rules="/[^0-9.]/g"
                class="form-control padding-left"
              />
            </td>
            <td class="table-row">
              <input
                v-model="factor.description"
                class="form-control padding-left"
              >
            </td>
            <td class="table-row padding-left">
              {{ factor.cpp_key }}
            </td>
            <td>
              <Treeselect
                v-model="factor.template_id"
                :options="templates.data"
                :disable-branch-nodes="true"
                :append-to-body="true"
                placeholder="Выберите шаблон"
              />
            </td>
            <td class="table-row">
              <div class="button">
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Сохранить фактор"
                  @click="updateFactor(factor)"
                >
                  <i class="fa fa-save" />
                </button>
                <button
                  v-tippy
                  class="btn last btn-blue-nb nbr"
                  title="Перейти к шаблону"
                  @click="showModal(factor.template_id)"
                >
                  <i class="fa fa-pencil" />
                </button>
              </div>
            </td>
          </tr>
        </table>
      </div>
    </div>
    <h4>
      Добавить фактор вредности
    </h4>
    <div>
      <table class="table table-bordered">
        <colgroup>
          <col width="150">
          <col>
          <col width="200">
          <col width="99">
        </colgroup>
        <tr>
          <td class="table-row">
            <RegexFormatInput
              v-model="title"
              :rules="/[^0-9.]/g"
              placeholder="Название"
              class="form-control padding-left"
            />
          </td>
          <td class="table-row">
            <input
              v-model="description"
              class="form-control padding-left"
              placeholder="Описание"
            >
          </td>
          <td>
            <Treeselect
              v-model="templateId"
              :disable-branch-nodes="true"
              :append-to-body="true"
              :options="templates.data"
              placeholder="Выберите шаблон"
            />
          </td>
          <td>
            <div class="button">
              <button
                v-tippy
                class="btn last btn-blue-nb nbr"
                title="Добавить фактор"
                @click="addFactor"
              >
                Добавить
              </button>
            </div>
          </td>
        </tr>
      </table>
    </div>
    <Modal
      v-if="modal"
      ref="modal"
      margin-top="30px"
      margin-left-right="auto"
      max-width="1500px"
      height="700px"
      show-footer="true"
      white-bg="true"
      width="100%"
      @close="hideModal"
    >
      <span slot="header">Редактирование шаблона</span>
      <div
        slot="body"
      >
        <iframe
          id="myframe"
          width="1470"
          height="605"
          :src="`/ui/construct/templates#{&quot;pk&quot;:${editTemplateId}}`"
        />
      </div>
      <div slot="footer">
        <div class="row">
          <div class="col-xs-10" />
          <div class="col-xs-2">
            <button
              class="btn btn-primary-nb btn-blue-nb"
              type="button"
              @click="hideModal"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script lang="ts">

import Treeselect from '@riophae/vue-treeselect';

import RegexFormatInput from '@/construct/RegexFormatInput.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import * as actions from '@/store/action-types';
import Modal from '@/ui-cards/Modal.vue';

export default {
  name: 'ConstructHarmfulFactor',
  components: { Treeselect, Modal, RegexFormatInput },
  data() {
    return {
      factors: [],
      templates: {},
      search: '',
      title: '',
      description: '',
      templateId: null,
      modal: false,
      editTemplateId: null,
    };
  },
  computed: {
    filteredFactors() {
      return this.factors.filter(factor => {
        const title = factor.title.toLowerCase();
        const description = factor.description.toLowerCase();
        const searchTerm = this.search.toLowerCase();

        return description.includes(searchTerm) || title.includes(searchTerm);
      });
    },
  },
  mounted() {
    this.getFactors();
    this.getTemplates();
  },
  methods: {
    async getFactors() {
      this.factors = await this.$api('/get-harmful-factors');
    },
    downloadHarmFullFactors() {
      window.open('/statistic/harmful-factors', '_blank');
    },
    async getTemplates() {
      this.templates = await this.$api('/get-templates');
    },
    showModal(templateId) {
      this.modal = true;
      this.editTemplateId = templateId;
    },
    hideModal() {
      this.modal = false;
      this.getTemplates();
      if (this.$refs.modal) {
        this.$refs.modal.$el.style.display = 'none';
      }
      this.$root.$emit('hide_template_editor');
    },
    async updateFactor(currentFactor) {
      if (!currentFactor.title || !currentFactor.template_id) {
        this.$root.$emit('msg', 'error', 'Данные не заполнены');
      } else if (this.factors.find((factor) => factor.title === currentFactor.title && factor.id !== currentFactor.id)) {
        this.$root.$emit('msg', 'error', 'Такое название уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/update-factor', currentFactor);
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
    async addFactor() {
      if (!this.title || !this.templateId) {
        this.$root.$emit('msg', 'error', 'Данные не заполнены');
      } else if (this.factors.find((factor) => factor.title === this.title)) {
        this.$root.$emit('msg', 'error', 'Такое название уже есть');
      } else {
        await this.$store.dispatch(actions.INC_LOADING);
        const { ok, message } = await this.$api('/add-factor', {
          title: this.title,
          description: this.description,
          templateId: this.templateId,
        });
        await this.$store.dispatch(actions.DEC_LOADING);
        if (ok) {
          this.$root.$emit('msg', 'ok', 'Сохранено');
          await this.getFactors();
          this.title = '';
          this.description = '';
          this.templateId = null;
        } else {
          this.$root.$emit('msg', 'error', message);
        }
      }
    },
  },
};
</script>

<style scoped>
::v-deep .form-control {
  border: none;
  padding: 6px 0;
  background-color: transparent;
}
::v-deep .vue-treeselect__control {
  border: 0;
}
::v-deep .card {
  margin: 1rem 0;
}
.table {
  margin-bottom: 0;
  table-layout: fixed;
}
.scroll {
  min-height: 111px;
  max-height: calc(100vh - 350px);
  overflow-y: auto;
}
.table-row {
  border: 1px solid #ddd;
  border-radius: 0;
}
.padding-left {
  padding-left: 6px;
}
.sticky {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: white;
}
.table > thead > tr > th {
  border-bottom: 0;
}
.search {
  border: 1px solid #ddd;
  border-radius: 5px;
  padding-left: 6px;
  background-color: white;
}
.button {
  width: 100%;
  display: flex;
  flex-wrap: nowrap;
  flex-direction: row;
  justify-content: stretch;
}
  .btn {
    align-self: stretch;
    flex: 1;
    padding: 7px 0;
  }

</style>
