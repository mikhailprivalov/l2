<template>
  <div v-frag>
    <div>
      <button
        class="btn btn-blue-nb btn-ell dropdown-toggle bt1"
        type="button"
        data-toggle="dropdown"
      >
        {{ selected_laboratory }}
        <span class="caret" />
      </button>
      <ul
        class="dropdown-menu"
        style="margin-top: 1px"
      >
        <li
          v-for="row in laboratories"
          :key="row.pk"
        >
          <a
            href="#"
            @click.prevent="laboratory = row.pk"
          >{{ row.title }}</a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script lang="ts">
import * as actions from '@/store/action-types';

export default {
  name: 'LaboratorySelector',
  props: {
    withAllLabs: {
      type: Boolean,
      required: false,
      default: false,
    },
    withForcedUpdateQuery: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      laboratories: [],
      laboratory: -1,
      useQuery: !!this.withForcedUpdateQuery,
    };
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
  watch: {
    laboratory: {
      handler() {
        this.emit();
        this.updateQuery();
      },
      immediate: true,
    },
  },
  async mounted() {
    await this.$store.dispatch(actions.INC_LOADING);

    const labPk = Number(this.$route.query.lab_pk);

    const { rows, active } = await this.$api('laboratory/laboratories');
    if (this.withAllLabs) {
      this.laboratory = -2;
      this.laboratories = [
        {
          pk: -2,
          title: 'Все лаборатории',
        },
        ...rows,
      ];
    } else {
      if (!Number.isNaN(labPk) && rows.some(l => l.pk === labPk)) {
        this.laboratory = labPk;
        this.useQuery = true;
      } else {
        this.laboratory = active;
      }
      this.laboratories = rows;
    }

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
  methods: {
    emit() {
      this.$root.$emit('change-laboratory', this.laboratory);
    },
    updateQuery() {
      if (this.useQuery) {
        this.$router.replace({
          query: {
            ...this.$route.query,
            lab_pk: this.laboratory,
          },
        });
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.bt1 {
  border-radius: 0;
  height: 36px;
  background-color: #656d78 !important;
  border: none !important;

  &:hover {
    background: #049372 !important;
  }
}
</style>
