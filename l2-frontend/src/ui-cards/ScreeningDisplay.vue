<template>
  <table class="table table-bordered table-condensed" style="table-layout: fixed">
    <colgroup>
      <col style="width: 170px"/>
      <col style="width: 47px"/>
      <col v-for="y in years" :key="y"/>
    </colgroup>
    <thead>
    <tr>
      <th class="text-center" :colspan="2 + years.length">План скрининга</th>
    </tr>
    <tr>
      <th colspan="2">Год</th>
      <td v-for="y in years" :key="y" :class="y === currentYear && 'current-param'">{{ y }}</td>
    </tr>
    <tr>
      <th colspan="2">Возраст</th>
      <td v-for="a in ages" :key="a" :class="a === patientAge && 'current-param'">{{ a }}</td>
    </tr>
    </thead>
    <tbody>
    <template v-for="r in researches">
      <tr :key="`${r.pk}_1`">
        <th rowspan="2">
          {{ r.title }} <a href="#" title="Выбрать для назначения" v-tippy class="a-under"
                           @click.prevent="addResearch(r.pk, r.title)"><i class="fas fa-circle"></i></a>
          <div class="plan-details">
            раз в {{r.period | pluralAge}}
          </div>
        </th>
        <th>план</th>
        <template v-for="(a, i) in r.ages">
          <td v-for="(v, j) in a.values" :key="`${i}_${j}`" class="cl-td fixed-td"
              :class="[
                a.isEven && 'td-even',
                v && (a.planYear !== v.year ? 'empty-plan' : 'has-plan'),
                !v ? 'no-plan' : 'plan',
                v && v.year >= currentYear && 'can-set-plan'
              ]">
            <div v-if="!v" />
            <div v-else-if="currentYear > v.year" class="plan-simple">
              <template v-if="a.planYear === v.year">
                {{ a.plan.replace(`.${v.year}`, '') }}
              </template>
            </div>
            <ScreeningDate v-else :a="a" :v="v" @updated="updatedDate"/>
          </td>
        </template>
      </tr>
      <tr :key="`${r.pk}_2`">
        <th>факт</th>
        <template v-for="(a, i) in r.ages">
          <td v-for="(v, j) in a.values" :key="`${i}_${j}`" class="cl-td fixed-td"
              :class="[a.isEven && 'td-even', !v && 'no-plan']">
            <div class="fact">
              <a href="#" @click.prevent="printResult(v.fact.direction)" class="a-under-reversed" v-if="v && v.fact">
                {{ v.fact.date.replace(`.${v.year}`, '') }}
              </a>
            </div>
          </td>
        </template>
      </tr>
    </template>
    </tbody>
  </table>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import ScreeningDate from '@/ui-cards/ScreeningDate.vue';

@Component({
  components: {
    ScreeningDate,
  },
  props: {
    patientAge: {
      type: Number,
      required: true,
    },
    currentYear: {
      type: Number,
      required: true,
    },
    years: {
      type: Array,
      required: true,
    },
    ages: {
      type: Array,
      required: true,
    },
    researches: {
      type: Array,
      required: true,
    },
  },
})
export default class ScreeningDisplay extends Vue {
  printResult(pk) {
    this.$root.$emit('print:results', [pk]);
  }

  updatedDate() {
    this.$forceUpdate();
  }

  addResearch(pk, title) {
    this.$root.$emit('msg', 'ok', `Выбрано: ${title}`, 3000);
    this.$root.$emit('researches-picker:add_research', pk);
  }
}
</script>

<style scoped lang="scss">
.fixed-td {
  &.no-plan {
    background-color: transparent !important;
  }

  background-color: #effbfd;

  &.has-plan {
    border-bottom: 3px solid #c2f0f7;
  }

  &.td-even {
    background-color: #fdf1ef;

    &.has-plan {
      border-bottom: 3px solid #f7c9c2;
    }
  }

  &.plan.can-set-plan {
    cursor: pointer;

    &:hover {
      background-color: #c2f0f7;
    }

    &.td-even:hover {
      background-color: #f7c9c2;
    }
  }
}

.fact, .plan-simple {
  height: 29px;
  line-height: 29px;
}

.table {
  height: 1px;

  td {
    text-align: center;
  }

  tr { height: 100%; }
  td { height: 100%; }
  td > div, td ::v-deep > div, td span, td ::v-deep > span { height: 100%; }
}

.plan-details {
  font-weight: normal;
  font-size: 12px;
}

.current-param {
  font-weight: bold;
}
</style>
