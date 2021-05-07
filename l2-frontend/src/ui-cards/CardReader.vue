<template>
  <div v-frag>
    <li v-show="Boolean(readerId)">
      <a href="#" @click.prevent="clickPlus" v-tippy title="Найти или импортировать пациента">
        <i class="fa fa-circle status" :class="`status-${status}`"></i> {{textStatus}}
      </a>
    </li>
  </div>
</template>

<script>
import usersPoint from '../api/user-point';
import * as actions from '../store/action-types';
import patientsPoint from '../api/patients-point';

export default {
  name: 'CardReader',
  data() {
    return {
      status: 'none',
      interval: null,
      readerId: window.localStorage.getItem('readerId'),
      fio: null,
      polis: null,
      details: {},
    };
  },
  mounted() {
    if (this.readerId) {
      this.loadReaderStatus();
    }
  },
  destroyed() {
    clearInterval(this.interval);
  },
  methods: {
    async loadReaderStatus() {
      const data = await usersPoint.loadReaderStatus({ readerId: this.readerId }).catch(() => ({}));
      this.status = data.status;
      this.fio = data.fio;
      this.polis = data.polis;
      this.details = data.details || {};

      this.interval = setTimeout(() => this.loadReaderStatus(), 1000);
    },
    click() {
      if (this.status !== 'inserted') {
        return;
      }

      this.$root.$emit('search-value', this.polis || '');
    },
    async clickPlus() {
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.createIndividualFromCard(this.details);
      await this.$store.dispatch(actions.DEC_LOADING);

      this.$root.$emit('search-value', this.polis || '');
    },
  },
  computed: {
    textStatus() {
      if (this.status === 'none') {
        return 'нет связи с карт-ридером';
      }
      if (this.status === 'wait') {
        return 'карта не вставлена в карт-ридер';
      }
      return `${this.fio} – ${this.polis}`;
    },
  },
};
</script>

<style lang="scss" scoped>
  .status {
    text-shadow: 0 0 1px #fff;
    display: inline-block;
    margin-right: 2px;

    &-none {
      color: #CF3A24
    }

    &-wait {
      color: #F4D03F
    }

    &-inserted {
      color: #049372;
    }
  }
</style>
