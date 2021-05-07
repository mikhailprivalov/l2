<template>
  <modal ref="modal" @close="hide" show-footer="true" white-bg="true"
         max-width="1024px" width="100%" marginLeftRight="auto" margin-top class="an">
    <span slot="header">Управление заявкой</span>
    <div slot="body" class="an-body">
      <div class="an-sidebar wide">
        <div class="an-sidebar-content">
          <div class="an-sidebar-content-row">
            <div class="an-sidebar-content-row-header">Номер:</div>
            {{ r.num }}{{ r.externalNum ? ` — ${r.externalNum}` : '' }}
            <div v-if="r.isMainExternal"><i class="fa fa-check"></i> в больнице</div>
          </div>
          <div class="an-sidebar-content-row">
            <div class="an-sidebar-content-row-header">Дата и время создания:</div>
            {{ r.createdAt }}&nbsp;{{ r.createdAtTime }}
          </div>
          <div class="an-sidebar-content-row">
            <div>{{ r.card }}, <strong>{{ r.phone }}</strong></div>
          </div>
          <div class="an-sidebar-content-row">
            <div>{{ r.address }}</div>
          </div>
          <div class="an-sidebar-content-row" v-if="r.email">
            {{ r.email }}
          </div>
          <div class="an-sidebar-content-row" v-if="r.hospital || r.district">
            <div>{{ r.hospital }}</div>
            <div>{{ r.district }}</div>
          </div>
          <div class="an-sidebar-content-row">
            <div class="an-sidebar-content-row-header">Цель:</div>
            <div>{{ r.purpose }}</div>
          </div>
          <div class="an-sidebar-content-row" v-if="r.research">
            <div class="an-sidebar-content-row-header">Услуга:</div>
            <div>{{ r.research }}</div>
          </div>
          <div class="an-sidebar-content-row" v-if="r.docAssigned">
            <div class="an-sidebar-content-row-header">Врач:</div>
            <div>{{ r.docAssigned }}</div>
          </div>
          <div class="an-sidebar-content-row" v-if="r.comment">
            <div class="an-sidebar-content-row-header">Примечания:</div>
            <div>{{ r.comment }}</div>
          </div>
          <div class="an-sidebar-content-row">
            <div class="an-sidebar-content-row-header">Исполнитель:</div>
            <div v-if="r.isMainExternal">
              внешняя больница
            </div>
            <div v-else-if="r.executor_fio">
              {{ r.executor_fio }}
            </div>
            <div v-else class="alert alert-warning" style="margin-bottom: 0">
              Не назначен!<br />
              <a href="#" @click.prevent="setMeAsExecutor" class="alert-link">Нажмите здесь, что бы стать исполнителем</a>
            </div>
            <div v-if="!r.isMainExternal && r.canEdit && r.executor_fio">
              <a href="#" @click.prevent="setMeAsExecutor" class="a-under">назначить меня</a>
            </div>
          </div>
          <div class="an-sidebar-content-row">
            <div class="an-sidebar-content-row-header">Статус:</div>
            <div>{{statusText}}</div>
          </div>
        </div>
      </div>
      <div class="an-content with-wide-sidebar">
        <DocCallLog :r="r"/>
      </div>
    </div>
    <div slot="footer">
      <div class="row">
        <div class="col-xs-5" style="float: right">
          <button @click="hide" class="btn btn-primary-nb btn-blue-nb" type="button">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </modal>
</template>

<script>
import api from '@/api';
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
    async setMeAsExecutor() {
      await this.$store.dispatch(actions.INC_LOADING);
      const {
        ok, message, status, executor, executor_fio, inLog,
      } = await api(
        'doctor-call/change-executor', this.r, ['pk'], { prevExecutor: this.r.executor },
      );
      if (!ok) {
        window.errmessage(message);
      } else {
        window.okmessage('Исполнитель обновлён успешно');
      }
      this.r.executor = executor;
      this.r.executor_fio = executor_fio;
      this.r.status = status;
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
