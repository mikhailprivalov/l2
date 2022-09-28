<template>
  <div v-frag>
    <div
      v-if="loading"
      class="text-center empty-screening"
    >
      загрузка скринингов
    </div>
    <table
      v-else-if="researches && researches.length > 0"
      class="table table-bordered table-condensed table-sm-pd"
      :style="yearWidth"
      :class="embedded && 'table-embedded-screening'"
    >
      <colgroup>
        <col>
        <col style="width: 47px">
        <col
          v-for="y in years"
          :key="y"
          class="col-year"
        >
      </colgroup>
      <thead>
        <tr>
          <th
            class="text-center"
            :colspan="2 + years.length"
          >
            План скрининга
          </th>
        </tr>
        <tr>
          <th colspan="2">
            Год
          </th>
          <td
            v-for="y in years"
            :key="y"
            :class="y === currentYear && 'current-param'"
          >
            {{ y }}
          </td>
        </tr>
        <tr>
          <th colspan="2">
            Возраст
          </th>
          <td
            v-for="a in ages"
            :key="a"
            :class="a === patientAge && 'current-param'"
          >
            {{ a }}
          </td>
        </tr>
      </thead>
      <tbody>
        <template v-for="r in researches">
          <tr :key="`${r.pk}_1`">
            <td
              rowspan="2"
              class="td-title"
            >
              <div v-if="!selectedResearches">
                {{ r.title }}
              </div>
              <ResearchPickById
                v-else
                :pk="r.pk"
                :selected-researches="selectedResearches"
                :kk="kk"
              />
              <div class="plan-details">
                раз в {{ r.period | pluralAge }}
              </div>
            </td>
            <th>план</th>
            <template v-for="(a, i) in r.ages">
              <td
                v-for="(v, j) in a.values"
                :key="`${i}_${j}`"
                class="cl-td fixed-td"
                :class="[
                  a.isEven && 'td-even',
                  v && (a.planYear !== v.year ? 'empty-plan' : 'has-plan'),
                  !v ? 'no-plan' : 'plan',
                  v && 'can-set-plan',
                ]"
              >
                <div v-if="!v" />
                <div v-else-if="embedded">
                  {{ a && a.plan && a.planYear === v.year ? a.plan.replace(`.${v.year}`, '') : '' }}
                </div>
                <ScreeningDate
                  v-else
                  :a="a"
                  :v="v"
                  :research-pk="r.pk"
                  @updated="updatedDate"
                />
              </td>
            </template>
          </tr>
          <tr :key="`${r.pk}_2`">
            <th>факт</th>
            <template v-for="(a, i) in r.ages">
              <td
                v-for="(v, j) in a.values"
                :key="`${i}_${j}`"
                class="cl-td fixed-td"
                :class="[a.isEven && 'td-even', !v && 'no-plan']"
              >
                <div class="fact">
                  <a
                    v-if="v && v.fact"
                    href="#"
                    class="a-under"
                    @click.prevent="printResult(v.fact.direction)"
                  >
                    {{ v.fact.date.replace(`.${v.year}`, '') }}
                  </a>
                </div>
              </td>
            </template>
          </tr>
        </template>
      </tbody>
    </table>
    <div
      v-else
      class="text-center empty-screening"
    >
      нет данных по скринингу
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import ScreeningDate from '@/ui-cards/ScreeningDate.vue';
import ResearchPickById from '@/ui-cards/ResearchPickById.vue';
import * as actions from '@/store/action-types';

@Component({
  components: {
    ResearchPickById,
    ScreeningDate,
  },
  props: {
    selectedResearches: {
      type: Array,
      required: false,
    },
    cardPk: {
      type: Number,
      required: true,
    },
    kk: {
      type: String,
      required: false,
    },
    embedded: {
      type: Boolean,
      required: false,
    },
    externalData: {
      type: Object,
      required: false,
    },
  },
  watch: {
    cardPk: {
      handler() {
        this.loadData();
      },
    },
  },
  data() {
    return {
      patientAge: -1,
      currentYear: -1,
      years: [],
      ages: [],
      researches: [],
      loading: true,
    };
  },
  mounted() {
    this.loadData();
  },
})
export default class ScreeningDisplay extends Vue {
  years: number[];

  ages: number[];

  cardPk: number;

  researches: any[];

  patientAge: number;

  currentYear: number;

  selectedResearches: any[];

  externalData: any;

  kk: any;

  loading: boolean;

  embedded: boolean;

  get yearWidth() {
    return `--year-width: calc(573px / ${this.years.length})`;
  }

  printResult(pk) {
    this.$root.$emit('print:results', [pk]);
  }

  async updatedDate(researchPk, ageGroup) {
    if (!this.embedded) {
      this.$forceUpdate();
      await this.$store.dispatch(actions.INC_LOADING);
    }
    await this.$api('/patients/save-screening-plan', {
      cardPk: this.cardPk,
      researchPk,
      ageGroup,
    });
    this.$root.$emit('updated:screening-plan');
    if (!this.embedded) {
      await this.$store.dispatch(actions.DEC_LOADING);
    }
  }

  addResearch(pk, title) {
    this.$root.$emit('msg', 'ok', `Выбрано: ${title}`, 3000);
    this.$root.$emit('researches-picker:add_research', pk);
  }

  async loadData() {
    this.loading = true;
    if (this.externalData) {
      const data = this.externalData;
      this.patientAge = data.patientAge;
      this.currentYear = data.currentYear;
      this.years = data.years;
      this.ages = data.ages;
      this.researches = data.researches;
    } else {
      const { data } = await this.$api('patients/individuals/load-screening', this, 'cardPk');
      this.patientAge = data.patientAge;
      this.currentYear = data.currentYear;
      this.years = data.years;
      this.ages = data.ages;
      this.researches = data.researches;
    }
    this.loading = false;
  }
}
</script>

<style scoped lang="scss">
$even_color: #4c4c4c;
$odd_color: #049372;
$normal_opacity: 0.3;
$hover_opacity: 0.45;
$border_mix_color: #fff;
$border_mix_percentage: 60%;

.fixed-td {
  &.no-plan {
    background-color: transparent !important;
  }

  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  font-weight: 600;

  background-color: rgba($odd_color, $normal_opacity);
  border-color: mix($odd_color, $border_mix_color, $border_mix_percentage);
  color: $odd_color;

  &.has-plan {
    border-bottom: 1px solid $odd_color;
  }

  a {
    color: $odd_color;
  }

  &.td-even {
    background-color: rgba($even_color, $normal_opacity);
    border-color: mix($even_color, $border_mix_color, $border_mix_percentage);
    color: $even_color;

    &.has-plan {
      border-bottom: 1px solid $even_color;
    }

    a {
      color: $even_color;
    }
  }

  &.plan.can-set-plan {
    cursor: pointer;

    &:hover {
      background-color: rgba($odd_color, $hover_opacity);
    }

    &.td-even:hover {
      background-color: rgba($even_color, $hover_opacity);
    }
  }
}

.fact,
.plan-simple {
  height: 27px;
  line-height: 27px;
}

.table {
  height: 1px;
  table-layout: fixed;
  font-size: 12px;

  td {
    text-align: center;
  }

  .td-title {
    text-align: left;
  }

  tr {
    height: 100%;
  }

  td {
    height: 100%;
  }

  td:not(.td-title) > div,
  td:not(.td-title) ::v-deep > div,
  td:not(.td-title) span,
  td:not(.td-title) ::v-deep > span {
    height: 100%;
  }
}

.plan-details {
  font-weight: normal;
  font-size: 11px;
  color: #777;
}

.current-param {
  font-weight: bold;
  background: rgba(0, 0, 0, 0.025);
}

.col-year {
  width: var(--year-width, 45px);
}

.empty-screening {
  padding: 20px;
  color: #7a7a7a;
}
</style>
