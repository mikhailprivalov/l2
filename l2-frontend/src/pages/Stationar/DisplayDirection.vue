<template>
  <div
    v-tippy="{
      html: '#tp-' + direction.pk,
      reactive: true,
      arrow: true,
      animation: 'fade',
      duration: 0,
      theme: 'light',
      interactive: true,
      placement: 'bottom',
      popperOptions: {
        modifiers: {
          preventOverflow: {
            boundariesElement: 'window',
          },
          hide: {
            enabled: false,
          },
        },
      },
    }"
    class="root-dd"
  >
    <div class="date">
      {{ direction.date_create }}
    </div>
    <div
      v-if="Boolean(direction.podrazdeleniye) && direction.researches.length !== 1"
      class="dep"
    >
      {{ direction.podrazdeleniye }}
    </div>
    <div
      v-else
      class="dep"
    >
      {{ direction.researches_short[0] || direction.researches[0] }}
    </div>
    <div
      v-if="idInPrintQueueStatus"
      style="float: right"
    >
      <i class="fa-solid fa-layer-group" />
    </div>

    <div
      :id="`tp-${direction.pk}`"
      class="tp"
    >
      <div class="t-left">
        <div>№ {{ direction.pk }}</div>
        <div>{{ direction.date_create }}</div>
      </div>
      <div class="t-right">
        <ul>
          <li><strong>Назначения:</strong></li>
          <li
            v-for="r in direction.researches"
            :key="r"
          >
            {{ r }}
          </li>
        </ul>
        <div
          v-if="direction.confirm"
          class="padding-plan-queue"
        >
          <a
            v-if="!idInPrintQueueStatus"
            href="#"
            style="float: right"
            @click.prevent="addIdToPlan"
          >В очередь печати</a>
          <a
            v-if="idInPrintQueueStatus"
            href="#"
            style="float: right"
            @click.prevent="delIdFromPlan"
          >Удалить из очереди</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">

import { PRINT_QUEUE_ADD_ELEMENT, PRINT_QUEUE_DEL_ELEMENT } from '@/store/action-types';

export default {
  name: 'DisplayDirection',
  props: ['direction'],
  computed: {
    idInPrintQueueStatus() {
      return this.$store.getters.idInQueue(this.direction.pk);
    },
  },
  methods: {
    addIdToPlan() {
      const id = [this.direction.pk];
      this.$store.dispatch(PRINT_QUEUE_ADD_ELEMENT, { id });
    },
    delIdFromPlan() {
      const id = this.direction.pk;
      this.$store.dispatch(PRINT_QUEUE_DEL_ELEMENT, { id });
    },
  },
};
</script>

<style scoped lang="scss">
.root-dd {
  padding: 3px;
  text-align: left;
  width: 100%;
  height: 100%;
  font-size: 12px;
}

.dep {
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.tp {
  text-align: left;
  line-height: 1.1;
  font-size: 14px;

  ul {
    padding-left: 20px;
    margin: 0;
  }
}

.t-left {
  width: 100px;
}

.t-right {
  max-width: 300px;
}

.t-left,
.t-right {
  display: inline-block;
  vertical-align: top;
}

.padding-plan-queue {
  padding-top: 10px;
}
</style>
