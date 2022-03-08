<template>
  <div v-frag>
    <ul
      v-show="Boolean(readerId)"
      class="nav navbar-nav"
    >
      <li>
        <a
          v-tippy
          href="#"
          title="Найти или импортировать пациента"
          @click.prevent="clickPlus"
        >
          <i
            class="fa fa-circle status"
            :class="`status-${status}`"
          /> {{ textStatus }}
        </a>
      </li>
    </ul>
  </div>
</template>

<script lang="ts">
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
      if (!this.polis) {
        this.$root.$emit('msg', 'error', 'Полис не считан');
        return;
      }
      await this.$store.dispatch(actions.INC_LOADING);
      await patientsPoint.createIndividualFromCard({
        ...this.details,
        polis: this.details.polis || this.polis,
      });
      await this.$store.dispatch(actions.DEC_LOADING);

      this.$root.$emit('search-value', this.polis || '');
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
    color: #cf3a24;
  }

  &-wait {
    color: #f4d03f;
  }

  &-inserted {
    color: #049372;
  }
}
</style>
