<template>
  <div v-frag>
    <td v-tippy="{html: '#template-' + r.pk + '-1', ...commonTippy}">
      {{ r.num }}{{ r.externalNum ? ` — ${r.externalNum}` : '' }}
      <div v-if="r.isMainExternal">в больнице</div>
    </td>
    <td v-tippy="{html: '#template-' + r.pk + '-2', ...commonTippy}">
      {{ r.createdAt }}<br/>
      {{ r.createdAtTime }}
    </td>
    <td v-tippy="{html: '#template-' + r.pk + '-3', ...commonTippy}">
      <div>{{ r.card }}</div>
      <div>{{ r.address }}</div>
      <div v-if="r.email">{{ r.email }}</div>
    </td>
    <td v-tippy="{html: '#template-' + r.pk + '-4', ...commonTippy}">{{ r.phone }}</td>
    <td v-tippy="{html: '#template-' + r.pk + '-5', ...commonTippy}">{{ r.purpose }}</td>
    <td v-tippy="{html: '#template-' + r.pk + '-6', ...commonTippy}">{{ r.comment }}</td>
    <td v-tippy="{html: '#template-' + r.pk + '-7', ...commonTippy}">
      <div v-if="r.isMainExternal">
        внешняя больница
      </div>
      <div v-else-if="r.executor_fio">
        {{ r.executor_fio }}
      </div>
      <div v-else>
        не назначен
      </div>
      <div v-if="!r.isMainExternal && r.canEdit">
        <a href="#" @click.prevent="setMeAsExecutor" class="a-under">назначить меня</a>
      </div>
    </td>
    <td v-tippy="{html: '#template-' + r.pk + '-8', ...commonTippy}">
      <select v-model="r.status" @change="onChangeStatus" :readonly="r.isMainExternal || !r.canEdit">
        <option :value="1">Новая заявка</option>
        <option :value="2">В работе</option>
        <option :value="3">Выполнено</option>
        <option :value="4">Отмена</option>
      </select>
    </td>
    <td>
      <button type="button" class="btn btn-blue-nb btn-sm" @click="showModal = true"
              v-if="!r.isMainExternal && r.canEdit" style="margin-top: 3px;">
        История заявки
      </button>

      <div>Записей: {{ r.inLog }}</div>

      <DocCallModal :r="r" v-if="showModal"/>
    </td>

    <div :id="`template-${r.pk}-${t}`" :key="t" class="tp" v-for="t in tpls">
      <div>
        Больница: {{ r.hospital || 'нет' }}
      </div>
      <div>
        Участок: {{ r.district || 'нет' }}
      </div>
      <div>
        Услуга: {{ r.research || 'нет' }}
      </div>
      <div>
        Врач: {{ r.docAssigned || 'нет' }}
      </div>
    </div>
  </div>
</template>
<script>
import api from '@/api';
import * as actions from '@/store/action-types';
import DocCallModal from '@/pages/DocCallModal.vue';

export default {
  name: 'DocCallRow',
  components: { DocCallModal },
  props: {
    r: {
      type: Object,
    },
  },
  data() {
    const tpls = [];
    for (let i = 1; i <= 8; i++) {
      tpls.push(i);
    }
    return {
      status: this.r.status,
      showModal: false,
      tpls,
      commonTippy: {
        reactive: true, animateFill: false, duration: 200, delay: [250, 0],
      },
    };
  },
  mounted() {
    this.$root.$on('doc-call:row:modal:hide', () => {
      this.showModal = false;
    });
    this.$root.$on('doc-call:status:updated', (pk) => {
      if (pk === this.r.pk) {
        this.status = this.r.status;
      }
    });
  },
  methods: {
    async onChangeStatus() {
      await this.$store.dispatch(actions.INC_LOADING);
      const {
        ok, message, status, executor, executor_fio, inLog,
      } = await api(
        'doctor-call/change-status', this.r, ['pk', 'status'], { prevStatus: this.status },
      );
      if (!ok) {
        window.errmessage(message);
      } else {
        window.okmessage('Статус обновлён успешно');
      }
      this.r.executor = executor;
      this.r.executor_fio = executor_fio;
      this.r.inLog = inLog;
      this.r.status = status;
      this.$root.$emit('doc-call:status:updated', this.r.pk);
      await this.$store.dispatch(actions.DEC_LOADING);
    },
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
      this.r.inLog = inLog;
      this.r.status = status;
      this.$root.$emit('doc-call:status:updated', this.r.pk);
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.tp {
  text-align: left;
  line-height: 1.1;
  font-size: 14px;
}
</style>
