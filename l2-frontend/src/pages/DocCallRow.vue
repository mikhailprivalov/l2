<template>
  <div v-frag>
    <td v-tippy="{ html: '#template-' + r.pk + '-1', ...commonTippy }">
      {{ r.num }}{{ r.externalNum ? ` — ${r.externalNum}` : '' }}
      <div v-if="r.isMainExternal">
        в больнице
      </div>
    </td>
    <td v-tippy="{ html: '#template-' + r.pk + '-2', ...commonTippy }">
      {{ r.createdAt }}<br>
      {{ r.createdAtTime }}
    </td>
    <td v-tippy="{ html: '#template-' + r.pk + '-3', ...commonTippy }">
      <div>{{ r.card }}</div>
      <div>{{ r.address }}</div>
      <div v-if="r.email">
        {{ r.email }}
      </div>
    </td>
    <td v-tippy="{ html: '#template-' + r.pk + '-4', ...commonTippy }">
      {{ r.phone }}
    </td>
    <td v-tippy="{ html: '#template-' + r.pk + '-5', ...commonTippy }">
      {{ r.purpose }}
      <div v-if="r.purpose_id === 24">
        {{ r.research }}
      </div>
    </td>
    <td v-tippy="{ html: '#template-' + r.pk + '-6', ...commonTippy }">
      {{ r.comment }}
      <div v-if="r.directionPk">
        <a
          href="#"
          class="a-under"
          @click.prevent="printProtocol(r.directionPk)"
        >просмотр</a>
      </div>
    </td>
    <td v-tippy="{ html: '#template-' + r.pk + '-7', ...commonTippy }">
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
        <a
          href="#"
          class="a-under"
          @click.prevent="setMeAsExecutor"
        >назначить меня</a>
      </div>
    </td>
    <td v-tippy="{ html: '#template-' + r.pk + '-8', ...commonTippy }">
      <select
        v-model="/* eslint-disable-line vue/no-mutating-props */ r.status"
        :readonly="r.isMainExternal || !r.canEdit"
        @change="onChangeStatus"
      >
        <option :value="1">
          Новая заявка
        </option>
        <option :value="2">
          В работе
        </option>
        <option :value="3">
          Выполнено
        </option>
        <option :value="4">
          Отмена
        </option>
      </select>
    </td>
    <td>
      <button
        v-if="!r.isMainExternal && r.canEdit"
        type="button"
        class="btn btn-blue-nb btn-sm"
        style="margin-top: 3px;"
        @click="showModal = true"
      >
        История заявки
      </button>

      <div>Записей: {{ r.inLog }}</div>

      <DocCallModal
        v-if="showModal"
        :r="r"
      />
    </td>

    <div
      v-for="t in tpls"
      :id="`template-${r.pk}-${t}`"
      :key="t"
      class="tp"
    >
      <div>Больница: {{ r.hospital || 'нет' }}</div>
      <div>Участок: {{ r.district || 'нет' }}</div>
      <div>Услуга: {{ r.research || 'нет' }}</div>
      <div>Врач: {{ r.docAssigned || 'нет' }}</div>
    </div>
  </div>
</template>

<script lang="ts">
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
        reactive: true,
        animateFill: false,
        duration: 200,
        delay: [250, 0],
      },
    };
  },
  mounted() {
    this.$root.$on('doc-call:row:modal:hide', () => {
      this.showModal = false;
    });
    this.$root.$on('doc-call:status:updated', pk => {
      if (pk === this.r.pk) {
        this.status = this.r.status;
      }
    });
  },
  methods: {
    printProtocol(pk) {
      this.$root.$emit('print:results', [pk]);
    },
    async onChangeStatus() {
      await this.$store.dispatch(actions.INC_LOADING);
      const {
        ok, message, status, executor, executor_fio: executorFio, inLog,
      } = await this.$api(
        'doctor-call/change-status',
        this.r,
        ['pk', 'status'],
        { prevStatus: this.status },
      );
      if (!ok) {
        this.$root.$emit('msg', 'error', message);
      } else {
        this.$root.$emit('msg', 'ok', 'Статус обновлён успешно');
      }
      // eslint-disable-next-line vue/no-mutating-props
      this.r.executor = executor;
      // eslint-disable-next-line vue/no-mutating-props
      this.r.executor_fio = executorFio;
      // eslint-disable-next-line vue/no-mutating-props
      this.r.inLog = inLog;
      // eslint-disable-next-line vue/no-mutating-props
      this.r.status = status;
      this.$root.$emit('doc-call:status:updated', this.r.pk);
      await this.$store.dispatch(actions.DEC_LOADING);
    },
    async setMeAsExecutor() {
      await this.$store.dispatch(actions.INC_LOADING);
      const {
        ok, message, status, executor, executor_fio: executorFio, inLog,
      } = await this.$api(
        'doctor-call/change-executor',
        this.r,
        ['pk'],
        {
          prevExecutor: this.r.executor,
        },
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
      this.r.inLog = inLog;
      // eslint-disable-next-line vue/no-mutating-props
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
