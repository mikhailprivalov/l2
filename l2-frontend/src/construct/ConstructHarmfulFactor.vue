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
      ref="modalRef"
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

<script setup lang="ts">
import Treeselect from '@riophae/vue-treeselect';
import {
  computed, getCurrentInstance, onMounted, ref,
} from 'vue';

import RegexFormatInput from '@/construct/RegexFormatInput.vue';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';
import api from '@/api';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';
import Modal from '@/ui-cards/Modal.vue';

const store = useStore();
const root = getCurrentInstance().proxy.$root;

const factors = ref<any[]>([]);
const templates = ref<any>({});
const search = ref('');
const title = ref('');
const description = ref('');
const templateId = ref<number | null>(null);
const modal = ref(false);
const editTemplateId = ref<number | null>(null);
const modalRef = ref<InstanceType<typeof Modal> | null>(null);

const filteredFactors = computed(() => factors.value.filter((factor) => {
  const factorTitle = factor.title.toLowerCase();
  const factorDescription = factor.description.toLowerCase();
  const searchTerm = search.value.toLowerCase();

  return factorDescription.includes(searchTerm) || factorTitle.includes(searchTerm);
}));

const getFactors = async () => {
  factors.value = await api('/get-harmful-factors');
};

const downloadHarmFullFactors = () => {
  window.open('/statistic/harmful-factors', '_blank');
};

const getTemplates = async () => {
  templates.value = await api('/get-templates');
};

const showModal = (id: number) => {
  modal.value = true;
  editTemplateId.value = id;
};

const hideModal = () => {
  modal.value = false;
  getTemplates();
  if (modalRef.value) {
    modalRef.value.$el.style.display = 'none';
  }
  root.$emit('hide_template_editor');
};

const updateFactor = async (currentFactor: any) => {
  if (!currentFactor.title || !currentFactor.template_id) {
    root.$emit('msg', 'error', 'Данные не заполнены');
  } else if (factors.value.find((factor) => factor.title === currentFactor.title && factor.id !== currentFactor.id)) {
    root.$emit('msg', 'error', 'Такое название уже есть');
  } else {
    await store.dispatch(actions.INC_LOADING);
    const { ok, message } = await api('/update-factor', currentFactor);
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      root.$emit('msg', 'ok', 'Сохранено');
    } else {
      root.$emit('msg', 'error', message);
    }
  }
};

const addFactor = async () => {
  if (!title.value || !templateId.value) {
    root.$emit('msg', 'error', 'Данные не заполнены');
  } else if (factors.value.find((factor) => factor.title === title.value)) {
    root.$emit('msg', 'error', 'Такое название уже есть');
  } else {
    await store.dispatch(actions.INC_LOADING);
    const { ok, message } = await api('/add-factor', {
      title: title.value,
      description: description.value,
      templateId: templateId.value,
    });
    await store.dispatch(actions.DEC_LOADING);
    if (ok) {
      root.$emit('msg', 'ok', 'Сохранено');
      await getFactors();
      title.value = '';
      description.value = '';
      templateId.value = null;
    } else {
      root.$emit('msg', 'error', message);
    }
  }
};

onMounted(() => {
  getFactors();
  getTemplates();
});
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
