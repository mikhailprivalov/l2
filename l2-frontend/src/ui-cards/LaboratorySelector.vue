<template>
  <div v-frag>
    <div>
      <button class="btn btn-blue-nb btn-ell dropdown-toggle bt1"
              type="button" data-toggle="dropdown">
        {{ selected_laboratory }}
        <span class="caret"></span>
      </button>
      <ul class="dropdown-menu" style="margin-top: 1px">
        <li v-for="row in laboratories" :key="row.pk">
          <a href="#" @click.prevent="laboratory = row.pk">{{ row.title }}</a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import * as actions from '@/store/action-types';
import api from '@/api';

export default {
  name: 'LaboratorySelector',
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);
    const { rows, active } = await api('laboratory/laboratories');
    this.laboratory = active;
    this.laboratories = rows;
    await this.$store.dispatch(actions.DEC_LOADING);
    this.$root.$on('emit-laboratory', () => {
      this.emit();
    });

    this.$root.$on('external-change-laboratory', (pk, cb) => {
      this.laboratory = pk;
      if (cb) {
        setTimeout(() => {
          cb();
        }, 300);
      }
    });
  },
  data() {
    return {
      laboratories: [],
      laboratory: -1,
    };
  },
  methods: {
    emit() {
      this.$root.$emit('change-laboratory', this.laboratory);
    },
  },
  watch: {
    laboratory: {
      handler() {
        this.emit();
      },
      immediate: true,
    },
  },
  computed: {
    selected_laboratory() {
      for (const l of this.laboratories) {
        if (l.pk === this.laboratory) {
          return l.title;
        }
      }

      return '';
    },
  },
};
</script>

<style lang="scss" scoped>
.bt1 {
  border-radius: 0;
  height: 36px;
  background-color: #656D78 !important;
  border: none !important;

  &:hover {
    background: #049372 !important;
  }
}
</style>
