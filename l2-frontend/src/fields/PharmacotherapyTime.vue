<template>
  <div v-if="data.empty" class="root" :data-datetime='data.datetime'>
    &nbsp;
  </div>
  <div v-else-if="data.ok" @click="setExecute(false)" class="root ok" :class="{hoverable: !data.cancel}"
       :data-datetime='data.datetime'
       :title="`${data.datetime}: Исполнитель: ${data.executor}${data.cancel ? '' : '. Отменить исполение'}`"
       v-tippy="{placement: 'top', arrow: true, animateFill: false}">
    ✓
  </div>
  <div v-else-if="data.cancel" class="root cancel"
       :data-datetime='data.datetime'
       :title="`${data.datetime}: Кто отменил: ${data.who_cancel}`"
       v-tippy="{placement: 'top', arrow: true, animateFill: false}">
    отм
  </div>
  <div v-else class="root wait" :class="{hoverable: !data.cancel}" @click="setExecute(true)"
       :data-datetime='data.datetime'
       :title="`${data.datetime}: не заполнено`" v-tippy="{placement: 'top', arrow: true, animateFill: false}">
    —
  </div>
</template>

<script>
import api from '@/api';
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
      const { ok, message } = await api('procedural-list/procedure-time-execute', { pk: this.data.pk, status });
      if (ok) {
        window.okmessage(message);
        this.$root.$emit('pharmacotherapy-aggregation:reload');
      } else {
        window.errmessage(message);
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
    background-color: rgba(#000, .18);
  }

  .ok {
    color: #049372;
    background-color: rgba(#049372, .12);
    &.hoverable:hover {
      background-color: rgba(#049372, .22);
    }
  }

  .cancel {
    color: #4B77BE;
    font-size: 10px;
  }
</style>
