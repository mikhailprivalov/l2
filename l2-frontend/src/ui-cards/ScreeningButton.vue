<template>
  <div v-frag>
    <a
      v-if="show"
      href="#"
      @click.prevent="open"
      class="main-open-link"
      v-tippy="{
        html: `#${tippyId}`,
        placement: 'bottom',
        arrow: true,
        reactive: true,
        interactive: true,
        theme: 'light bordered',
        zIndex: 4999,
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
      :class="{ [`screening_${status}`]: true }"
    >
      Скрининг
    </a>

    <div :id="tippyId" class="tp" v-if="show">
      <ScreeningDisplay :card-pk="cardPk" :external-data="data" embedded />
      <button class="btn btn-blue-nb" @click="open">Открыть скрининг</button>
      <div class="text-center"><small>для настройки и создания направлений</small></div>
    </div>
  </div>
</template>

<script lang="ts">
import api from '@/api';

export default {
  name: 'ScreeningButton',
  components: {
    ScreeningDisplay: () => import('@/ui-cards/ScreeningDisplay.vue'),
  },
  props: {
    cardPk: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      data: {},
      loading: false,
    };
  },
  computed: {
    tippyId() {
      return `screening-button-${this.cardPk}`;
    },
    show() {
      return this.data.researches && this.data.researches.length > 0;
    },
    status() {
      const { patientAge, researches } = this.data;
      let hasNoFeaturePlan = false;
      let hasNoCurrentFact = false;

      for (const r of researches) {
        for (const a of r.ages) {
          const ages = (a.values || []).map(x => (x ? x.age : null));
          const facts = (a.values || []).map(x => x?.fact).filter(Boolean);

          if (ages.length === 0 || ages[ages.length - 1] < patientAge) {
            continue;
          }

          if (ages.includes(patientAge) && facts.length === 0) {
            hasNoCurrentFact = true;
            continue;
          }

          if (!ages.includes(patientAge) && ages[0] !== null && ages[0] === patientAge + 1 && !a.plan) {
            hasNoFeaturePlan = true;
            continue;
          }
        }
      }

      if (hasNoCurrentFact) {
        return 'error';
      }

      if (hasNoFeaturePlan) {
        return 'warning';
      }

      return 'none';
    },
  },
  mounted() {
    this.load();
    this.$root.$on('updated:screening-plan', () => this.load());
  },
  methods: {
    async load() {
      this.loading = true;
      const { data } = await api('patients/individuals/load-screening', this, 'cardPk');
      this.data = data;
      this.loading = false;
    },
    open() {
      this.$emit('openScreening');
    },
  },
  watch: {
    cardPk: {
      handler() {
        this.load();
      },
    },
  },
};
</script>

<style scoped lang="scss">
.main-open-link {
  margin-left: 3px;
  font-size: 12px;
}

.tp {
  text-align: left;
  padding: 1px;

  max-width: 1000px;

  .btn {
    width: 100%;
    padding: 4px;
  }
}

.screening {
  &_error {
    color: #da3b6c;
    text-shadow: 0 0 4px rgba(#da3b6c, 0.6);
  }

  &_warning {
    color: #da8e3b;
    text-shadow: 0 0 4px rgba(#da8e3b, 0.6);
  }
}
</style>
