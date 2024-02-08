<template>
  <ul class="nav navbar-nav">
    <li class="dropdown">
      <a
        v-tippy="{
          html: '#print-queue-view',
          reactive: true,
          interactive: true,
          arrow: true,
          animation: 'fade',
          duration: 0,
          theme: 'light',
          placement: 'bottom',
          trigger: 'click mouseenter',
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
        href="#"
        class="dropdown-toggle"
        @click.prevent
        @show="load"
      >
        Очередь печати <span class="badge badge-light">{{ printQueueCount }}</span></a>
      <div
        id="print-queue-view"
        class="tp"
      >
        <a
          class="a-btn a-left-padding"
          href="#"
          @click.prevent="print"
        >Печать</a>
        <a
          class="a-btn"
          href="#"
          @click.prevent="flushPlan"
        >Очистить</a>
        <table class="table table-condensed table-bordered">
          <colgroup>
            <col style="width: 70px">
            <col style="width: 100px">
            <col style="width: 120px">
            <col style="width: 90px">
            <col style="width: 300px">
            <col style="width: 40px">
          </colgroup>
          <thead>
            <tr>
              <th>Порядок</th>
              <th>Номер</th>
              <th>Тип</th>
              <th>Дата</th>
              <th>Услуга</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, index) in dataDirections"
              :key="index"
            >
              <td class="td-align">
                <a
                  href="#"
                  @click.prevent="updateOrder('up', index)"
                >
                  <i class="fa-solid fa-arrow-up" />
                </a>
                <a
                  class="a-left-padding"
                  href="#"
                  @click.prevent="updateOrder('down', index)"
                >
                  <i class="fa-solid fa-arrow-down" />
                </a>
              </td>
              <td>
                <ResultDetails
                  :direction="row.direction"
                  :is-lab="row.isLab"
                  :is-doc-referral="row.isDocReferral"
                  :is-paraclinic="row.isParaclinic"
                />
              </td>
              <td>
                {{ row.type }}
              </td>
              <td>
                {{ row.timeConfirm }}
              </td>
              <td class="researches">
                {{ row.researches }}
              </td>
              <td class="td-align">
                <a
                  v-tippy
                  title="Удалить из очереди"
                  href="#"
                  @click.prevent="delIdFromPlan(row.direction)"
                >
                  <i class="fa fa-times" />
                </a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </li>
  </ul>
</template>

<script lang="ts">

import { PRINT_QUEUE_CHANGE_ORDER, PRINT_QUEUE_DEL_ELEMENT, PRINT_QUEUE_FLUSH } from '@/store/action-types';

import ResultDetails from './PatientResults/ResultDetails.vue';

export default {
  name: 'PrintQueue',
  components: { ResultDetails },
  data() {
    return {
      dataDirections: [],
    };
  },
  computed: {
    printQueueCount() {
      return this.$store.getters.printQueueCount;
    },
    currentPrintQueue() {
      return this.$store.getters.stateCurrentPrintQueue;
    },
  },
  mounted() {
    this.load();
  },
  methods: {
    async load() {
      const { rows } = await this.$api('directions/meta-info', { directions: this.currentPrintQueue });
      this.dataDirections = rows;
    },
    print() {
      window.open(`results/preview?pk=[${this.currentPrintQueue}]&hosp=1&sort=1`, '_blank');
    },
    delIdFromPlan(id) {
      this.$store.dispatch(PRINT_QUEUE_DEL_ELEMENT, { id });
      this.load();
    },
    flushPlan() {
      this.$store.dispatch(PRINT_QUEUE_FLUSH);
      this.load();
    },
    updateOrder(typeOrder, index) {
      if (((index === 0) && (typeOrder !== 'up'))
          || ((index === this.dataDirections.length - 1) && (typeOrder !== 'down'))
          || ((index !== 0) && (index !== this.dataDirections.length - 1))) {
        this.$store.dispatch(PRINT_QUEUE_CHANGE_ORDER, { typeOrder, index });
        this.load();
      }
    },
  },
};

</script>

<style scoped lang="scss">
i {
  vertical-align: middle;
  display: inline-block;
  margin-right: 3px;
}

.tp {
  min-height: 350px;
  text-align: left;
  line-height: 1.1;
  padding: 5px;

  table {
    margin: 0;
    table-layout: fixed;
  }
  max-height: 600px;
  overflow-y: auto;
  max-width: 800px;
}

.researches {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.td-align {
  text-align: center;
}
a {
  color: grey;
}
.a-btn {
  color: #3BAFDA;
  padding-bottom: 15px;
  padding-top: 5px;
  float: right;
}

.a-left-padding {
  padding-left: 10px;
}

</style>
