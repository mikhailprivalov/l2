<template>
  <fragment>
    <td>
      {{ r.num }}{{ r.externalNum ? ` — ${r.externalNum}` : '' }}
      <div v-if="r.isMainExternal">в больнице</div>
    </td>
    <td>
      {{ r.createdAt }}<br/>
      {{ r.createdAtTime }}
    </td>
    <td>{{ r.execAt }}</td>
    <td>
      <div>{{ r.card }}</div>
      <div>{{ r.address }}</div>
      <div v-if="r.email">{{r.email}}</div>
    </td>
    <td>
      {{ r.hospital }}<br/>
      {{ r.district }}
    </td>
    <td>{{ r.phone }}</td>
    <td>{{ r.purpose }}</td>
    <td>
      {{ r.research }}<br/>
      {{ r.docAssigned }}
    </td>
    <td>{{ r.comment }}</td>
    <td>
      <div v-if="r.isMainExternal">
        внешняя больница
      </div>
      <div v-else-if="r.executor_fio">
        {{r.executor_fio}}
      </div>
      <div v-else>
        не назначен
      </div>
      <div v-if="!r.isMainExternal && !r.canEdit">
        <a href="#" @click.prevent="setMeAsExecutor" class="a-under">назначить меня</a>
      </div>
    </td>
    <td>
      <select v-model="r.status" @change="onChangeStatus" :readonly="r.isMainExternal || !r.canEdit">
        <option :value="1">Новая заявка</option>
        <option :value="2">В работе</option>
        <option :value="3">Выполнено</option>
        <option :value="4">Отмена</option>
      </select>
    </td>
  </fragment>
</template>
<script>
import api from '@/api';
import * as action_types from "@/store/action-types";

export default {
  name: 'DocCallRow',
  props: {
    r: {
      type: Object,
    }
  },
  data() {
    return {
      status: this.r.status,
    }
  },
  methods: {
    async onChangeStatus() {
      await this.$store.dispatch(action_types.INC_LOADING);
      const {ok, message, status, executor, executor_fio} = await api(
        'doctor-call/change-status', this.r, ['pk', 'status'], {prevStatus: this.status}
      );
      if (!ok) {
        errmessage(message);
      } else {
        okmessage('Статус обновлён успешно');
      }
      this.r.executor = executor;
      this.r.executor_fio = executor_fio;
      this.status = this.r.status = status;
      await this.$store.dispatch(action_types.DEC_LOADING);
    },
    async setMeAsExecutor() {
      await this.$store.dispatch(action_types.INC_LOADING);
      const {ok, message, status, executor, executor_fio} = await api(
        'doctor-call/change-executor', this.r, ['pk'], {prevExecutor: this.r.executor}
      );
      if (!ok) {
        errmessage(message);
      } else {
        okmessage('Исполнитель обновлён успешно');
      }
      this.r.executor = executor;
      this.r.executor_fio = executor_fio;
      this.status = this.r.status = status;
      await this.$store.dispatch(action_types.DEC_LOADING);
    },
  },
}
</script>
