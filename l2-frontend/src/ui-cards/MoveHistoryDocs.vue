<template>
  <ul class="nav navbar-nav">
    <li>
      <a
        href="#"
        @click.prevent="moveDocs = true"
      >Перенести документы</a>
      <Modal
        v-if="moveDocs"
        ref="modal"
        show-footer="true"
        white-bg="true"
        max-width="680px"
        width="100%"
        margin-left-right="auto"
        margin-top
        @close="hideMoveDocs"
      >
        <span slot="header">Перемещение документов</span>
        <div
          slot="body"
          style="min-height: 200px"
          class="registry-body"
        >
          <div>
            <div class="form-row">
              <div class="row-t">
                Пациент (карта)
              </div>
              <input
                v-model="patientFio"
                class="form-control"
                readonly
              >
            </div>
            <div class="form-row">
              <div class="row-t">
                № Истории
              </div>
              <input
                v-model="currentDirectionHistoryOpen"
                class="form-control"
                readonly
              >
            </div>
            <div class="form-row">
              <div class="row-t">
                Номер целевой истории
              </div>
              <div class="row-v">
                <input
                  v-model="targetHistory"
                  class="form-control"
                >
              </div>
            </div>
            <div class="form-row">
              <div class="row-t document-label-group">
                <label>Документы</label>
                <button
                  type="button"
                  class="checkbox-btn"
                  :class="{ active: checkBoxAllDocuments }"
                  @click="checkBoxAllDocuments = !checkBoxAllDocuments"
                >
                  {{ checkBoxAllDocuments ? '✓ Все' : '☐ Все' }}
                </button>
              </div>
              <div class="row-v">
                <input
                  v-model="targetDocument"
                  class="form-control"
                  :readonly="checkBoxAllDocuments"
                  :placeholder="checkBoxAllDocuments ? 'Будут перенесены все документы' : 'Введите номер документа'"
                >
              </div>
            </div>
            <div class="buttons">
              <button
                class="btn btn-blue-nb btn-sm"
                :class="[{ btndisable: !targetHistory || (!checkBoxAllDocuments && !targetDocument) }]"
                @click="moveDocsExecute"
              >
                Перенести документы
              </button>
            </div>
          </div>
        </div>
        <div slot="footer">
          <div class="row">
            <div
              class="col-xs-5"
              style="float: right"
            >
              <button
                class="btn btn-primary-nb btn-blue-nb"
                type="button"
                @click="hideMoveDocs"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      </Modal>
    </li>
  </ul>
</template>

<script setup lang="ts">
import {
  getCurrentInstance, onMounted, ref, watch,
} from 'vue';

import Modal from '@/ui-cards/Modal.vue';
import api from '@/api';
import * as actions from '@/store/action-types';
import { useStore } from '@/store';

const store = useStore();
const root = getCurrentInstance().proxy.$root;
const refs = getCurrentInstance().proxy.$refs;

const moveDocs = ref(false);
const cardPk = ref(null);
const patientFio = ref('');
const targetHistory = ref(null);
const targetDocument = ref(null);
const checkBoxAllDocuments = ref(true);
const currentDirectionHistoryOpen = ref('');

watch(checkBoxAllDocuments, (oldValue) => {
  if (oldValue) {
    targetDocument.value = null;
  }
});

const hideMoveDocs = () => {
  root.$emit('hide_move_docs');
};

const moveDocsExecute = async () => {
  const { histOk } = await api('directions/is-history', { target_history: targetHistory.value });
  if (!histOk) {
    root.$emit('msg', 'error', 'История не найдена');
    return;
  }

  const targetDocumentId = ref(-1);
  if (targetDocument.value) {
    targetDocumentId.value = targetDocument.value;
  }

  const { docOk } = await api('directions/is-document', { target_document: targetDocumentId.value });
  if (!docOk) {
    root.$emit('msg', 'error', 'Документ не найден');
    return;
  }

  await store.dispatch(actions.INC_LOADING);
  const data = await api('directions/change-parent-direction', {
    old_history_number: currentDirectionHistoryOpen.value,
    new_history_number: targetHistory.value,
    target_document_number: targetDocumentId.value,
  });
  root.$emit('msg', 'ok', 'Документы успешно перенесены');
  root.$emit('msg', 'ok', `Номера: ${data.directions}`);
  await store.dispatch(actions.DEC_LOADING);

  hideMoveDocs();
  root.$emit('open-history', currentDirectionHistoryOpen.value);
};

onMounted(() => {
  root.$on('current_history_direction', (data) => {
    currentDirectionHistoryOpen.value = data.history_num;
    cardPk.value = data.patient.card_pk;
    patientFio.value = data.patient.fio_age?.split('+')[0];
  });
  root.$on('hide_move_docs', () => {
    if (refs.modal) {
      refs.modal.$el.style.display = 'none';
      targetHistory.value = null;
      targetDocument.value = null;
      checkBoxAllDocuments.value = true;
      moveDocs.value = false;
    }
  });
});
</script>

<style scoped lang="scss">
  ::v-deep .panel-flt {
    margin: 41px;
    align-self: stretch !important;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  ::v-deep .panel-body {
    flex: 1;
    padding: 0;
    height: calc(100% - 91px);
    min-height: 200px;
  }

  .document-label-group {
    display: flex !important;
    padding: 0 !important;
    background: #aab2bd;

    label {
      flex: 1;
      padding: 7px 0 0 10px;
      color: #fff;
      width: auto !important;
      font-weight: normal;
      font-size: 14px;
      margin: 0;
      cursor: default;
    }

    .checkbox-btn {
      width: 70px;
      background: #aab2bd;
      border: none;
      border-left: 1px solid #434a54;
      cursor: pointer;
      font-size: 14px;
      font-weight: normal;
      transition: all 0.2s;
      color: #fff;

      &:hover {
        background: #8f9aa6;
        color: #fff;
      }

      &.active {
        background: #049372;
        color: white;
        border-left: 1px solid transparent;

        &:hover {
          background: #037f5c;
        }
      }
    }
  }

  .form-row {
    width: 100%;
    display: flex;
    border-bottom: 1px solid #434a54;

    &:first-child:not(.nbt-i) {
      border-top: 1px solid #434a54;
    }

    justify-content: stretch;

    .row-t {
      background-color: #aab2bd;
      padding: 7px 0 0 10px;
      width: 35%;
      flex: 0 35%;
      color: #fff;
    }

    .input-group {
      flex: 0 65%;
    }

    input,
    .row-v,
    ::v-deep input {
      background: #fff;
      border: none;
      border-radius: 0 !important;
      width: 60%;
      flex: 0 65%;
      height: 36px;
    }

    &.sm-f {
      .row-t {
        padding: 2px 0 0 10px;
      }

      input,
      .row-v,
      ::v-deep input {
        height: 26px;
      }
    }

    ::v-deep input {
      width: 100% !important;
    }

    .row-v {
      padding: 0 0 0 0;
    }

    ::v-deep .input-group {
      border-radius: 0;
    }
  }

  .buttons {
    padding: 10px;
    text-align: center;
  }

  .btndisable {
    cursor: not-allowed;
    pointer-events: none;

    color: #c0c0c0;
    background-color: #ffffff;
  }
</style>
