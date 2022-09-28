<template>
  <Modal
    ref="modal"
    show-footer="true"
    white-bg="true"
    max-width="1024px"
    width="100%"
    margin-left-right="auto"
    margin-top
    class="an"
    @close="hide"
  >
    <span slot="header">Управление заявкой</span>
    <div
      slot="body"
      class="an-body"
    >
      <div class="an-sidebar wide">
        <div class="an-sidebar-content">
          <div class="an-sidebar-content-row">
            <div class="an-sidebar-content-row-header">
              Номер:
            </div>
            {{ r.num }}{{ r.externalNum ? ` — ${r.externalNum}` : '' }}
            <div v-if="r.isMainExternal">
              <i class="fa fa-check" /> в больнице
            </div>
          </div>
          <div class="an-sidebar-content-row">
            <div class="an-sidebar-content-row-header">
              Дата и время создания:
            </div>
            {{ r.createdAt }}&nbsp;{{ r.createdAtTime }}
          </div>
          <div class="an-sidebar-content-row">
            <div>
              {{ r.card }}, <strong>{{ r.phone }}</strong>
            </div>
          </div>
          <div class="an-sidebar-content-row">
            <div>{{ r.address || 'нет адреса' }}</div>
          </div>
          <div
            v-if="r.email"
            class="an-sidebar-content-row"
          >
            {{ r.email }}
          </div>
          <div
            v-if="r.hospital || r.district"
            class="an-sidebar-content-row"
          >
            <div>{{ r.hospital }}</div>
            <div>{{ r.district }}</div>
          </div>
          <div class="an-sidebar-content-row">
            <div class="an-sidebar-content-row-header">
              Цель:
            </div>
            <div>{{ r.purpose }}</div>
          </div>
          <div
            v-if="r.research"
            class="an-sidebar-content-row"
          >
            <div class="an-sidebar-content-row-header">
              Услуга:
            </div>
            <div>{{ r.research }}</div>
          </div>
          <div
            v-if="r.docAssigned"
            class="an-sidebar-content-row"
          >
            <div class="an-sidebar-content-row-header">
              Врач:
            </div>
            <div>{{ r.docAssigned }}</div>
          </div>
          <div
            v-if="r.comment"
            class="an-sidebar-content-row"
          >
            <div class="an-sidebar-content-row-header">
              Примечания:
            </div>
            <div>{{ r.comment }}</div>
          </div>
          <div
            v-if="r.directionPk"
            class="an-sidebar-content-row"
          >
            <div class="an-sidebar-content-row-header">
              Связанный протокол:
            </div>
            <div>
              <a
                href="#"
                class="a-under"
                @click.prevent="printProtocol(r.directionPk)"
              >просмотр</a>
            </div>
          </div>
          <div class="an-sidebar-content-row">
            <div class="an-sidebar-content-row-header">
              Исполнитель:
            </div>
            <div v-if="r.isMainExternal">
              внешняя больница
            </div>
            <div v-else-if="r.executor_fio">
              {{ r.executor_fio }}
            </div>
            <div
              v-else
              class="alert alert-warning"
              style="margin-bottom: 0"
            >
              Не назначен!<br>
              <a
                href="#"
                class="alert-link"
                @click.prevent="setMeAsExecutor"
              >Нажмите здесь, что бы стать исполнителем</a>
            </div>
            <div v-if="!r.isMainExternal && r.canEdit && r.executor_fio">
              <a
                href="#"
                class="a-under"
                @click.prevent="setMeAsExecutor"
              >назначить меня</a>
            </div>
          </div>
          <div class="an-sidebar-content-row">
            <div class="an-sidebar-content-row-header">
              Статус:
            </div>
            <div>{{ statusText }}</div>
          </div>
        </div>
      </div>
      <div class="an-content with-wide-sidebar">
        <DocCallLog :r="r" />
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
import * as actions from '@/store/action-types';
import Modal from '@/ui-cards/Modal.vue';

import DocCallLog from './DocCallLog.vue';

export default {
  name: 'DocCallModal',
  components: { Modal, DocCallLog },
  props: {
    r: {
      type: Object,
    },
  },
  computed: {
    statusText() {
      return {
        1: 'Новая заявка',
        2: 'В работе',
        3: 'Выполнено',
        4: 'Отмена',
      }[this.r.status];
    },
  },
  methods: {
    printProtocol(pk) {
      this.$root.$emit('print:results', [pk]);
    },
    async setMeAsExecutor() {
      await this.$store.dispatch(actions.INC_LOADING);
      const {
        ok, message, status, executor, executor_fio: executorFio, inLog,
      } = await this.$api(
        'doctor-call/change-executor',
        this.r,
        ['pk'],
        { prevExecutor: this.r.executor },
      );
      if (!ok) {
        this.$root.$emit('msg', 'error', message);
      } else {
        this.$root.$emit('msg', 'ok', 'Исполнитель обновлён успешно');
      }
      // eslint-disable-next-line vue/no-mutating-props
      this.r.executor = executor;
      // eslint-disable-next-line vue/no-mutating-props
      this.r.executor_fio = executorFio;
      // eslint-disable-next-line vue/no-mutating-props
      this.r.status = status;
      // eslint-disable-next-line vue/no-mutating-props
      this.r.inLog = inLog;
      this.$root.$emit('doc-call:log:update');
      this.$root.$emit('doc-call:status:updated', this.r.pk);
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
