<template>
  <div
    v-if="data.empty"
    class="root"
    :data-datetime="data.datetime"
  >
    &nbsp;
  </div>
  <div
    v-else-if="data.ok"
    v-tippy="{ placement: 'top', arrow: true, animateFill: false }"
    class="root ok"
    :class="{ hoverable: !data.cancel }"
    :data-datetime="data.datetime"
    :title="`${data.datetime}: Исполнитель: ${data.executor}${data.cancel ? '' : '. Отменить исполение'}`"
    @click="setExecute(false)"
  >
    ✓
  </div>
  <div
    v-else-if="data.cancel"
    v-tippy="{ placement: 'top', arrow: true, animateFill: false }"
    class="root cancel"
    :data-datetime="data.datetime"
    :title="`${data.datetime}: Кто отменил: ${data.who_cancel}`"
  >
    отм
  </div>
  <div
    v-else
    v-tippy="{ placement: 'top', arrow: true, animateFill: false }"
    class="root wait"
    :class="{ hoverable: !data.cancel }"
    :data-datetime="data.datetime"
    :title="`${data.datetime}: не заполнено`"
    @click="setExecute(true)"
  >
    —
  </div>
</template>

<script lang="ts">
import * as actions from '@/store/action-types';

export default {
  name: 'PharmacotherapyTime',
  props: {
    data: {},
  },
  methods: {
    async setExecute(status) {
      if (!status) {
        try {
          await this.$dialog.confirm('Вы действительно хотите произвести сброс выполнения?');
        } catch (_) {
          return;
        }
      }
      await this.$store.dispatch(actions.INC_LOADING);
      this.data.ok = status;
      this.data.executor = 'загрузка...';
      const { ok, message } = await this.$api('procedural-list/procedure-time-execute', { pk: this.data.pk, status });
      if (ok) {
        this.$root.$emit('msg', 'ok', message);
        this.$root.$emit('pharmacotherapy-aggregation:reload');
      } else {
        this.$root.$emit('msg', 'error', message);
      }
      await this.$store.dispatch(actions.DEC_LOADING);
    },
  },
};
</script>

<style scoped lang="scss">
.root {
  display: inline-block;
  width: 30px;
  text-align: center;
  height: 24px;
  vertical-align: middle;

  //&:nth-child(odd) {
  //  background-color: rgba(#000, .045);
  //  &.ok {
  //    background-color: rgba(#049372, .18);
  //  }
  //}
}

.hoverable:hover {
  cursor: pointer;
  background-color: rgba(#000, 0.18);
}

.ok {
  color: #049372;
  background-color: rgba(#049372, 0.12);
  &.hoverable:hover {
    background-color: rgba(#049372, 0.22);
  }
}

.cancel {
  color: #4b77be;
  font-size: 10px;
}
</style>
