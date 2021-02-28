<template>
  <div class="root">
    <table class="table table-bordered table-condensed table-responsive">
      <colgroup>
        <col width="26%">
        <col width="32%">
        <col width="21%">
        <col width="21%">
      </colgroup>
      <tbody>
      <tr>
        <th>№ направл.</th>
        <td>
          <a v-if="direction.pk" :href='`/directions/pdf?napr_id=[${direction.pk}]`' target='_blank' class="a-under">
            {{ direction.pk }}
          </a>
        </td>
        <th>Финанс.</th>
        <td>
          {{ direction.fin_source }}
          <template v-if="fromRmis">внеш.орг</template>
        </td>
      </tr>
      <tr>
        <th>Пациент</th>
        <td :colspan="patient.diagnosis ? 2 : 3">
          {{ patient.fio }}
        </td>
        <td v-if="patient.diagnosis" title="Диагноз" v-tippy>
          {{ patient.diagnosis }}
        </td>
      </tr>
      <tr>
        <th>Пол</th>
        <td>{{ patient.sex }}</td>
        <th>Возраст</th>
        <td>{{ patient.age }}</td>
      </tr>
      <tr v-if="patient.history_num">
        <th>Карта</th>
        <td>{{ patient.card }}</td>
        <th>Истор.</th>
        <td title="Номер истории" v-tippy>{{ patient.history_num }}</td>
      </tr>
      <tr v-else>
        <th>Карта</th>
        <td colspan="3">{{ patient.card }}</td>
      </tr>
      <tr title="Лечащий врач" v-if="!fromRmis" v-tippy>
        <th>Леч. врач</th>
        <td colspan="3">{{ direction.directioner }}</td>
      </tr>
      <tr v-if="!fromRmis">
        <th>Отделение</th>
        <td colspan="3">{{ direction.otd }}</td>
      </tr>
      <tr v-if="fromRmis">
        <th>Организация</th>
        <td colspan="3">{{ direction.imported_org }}</td>
      </tr>
      </tbody>
    </table>
    <div class="issledovaniya-scroll-wrapper">
      <ul class="issledovaniya">
        <li
          :class='[
          `issledovaniya-isnorm-${i.is_norm}`,
          active !== i.pk && `tb-group-${i.group}`,
          active === i.pk && `tb-group-full-${i.group} tb-group-active-${i.group} active`
        ]'
          @click="select(i.pk)"
          v-for="i in issledovaniya">
          <div :class='`status status-${getStatusClass(i)}`'>{{ getStatus(i) }}</div>
          {{ i.title }}
          <br/>
          <small v-if="i.tubes.length > 0">Ёмкость: {{ i.tubes.map(t => t.pk).join(', ') }}</small>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import _ from 'lodash';

export default {
  name: "DirectionForm",
  data() {
    return {
      direction: {},
      patient: {},
      issledovaniya: [],
      loaded: false,
      active: -1,
    };
  },
  mounted() {
    this.$root.$on('laboratory:results:show-direction', data => {
      this.direction = data.direction;
      this.patient = data.patient;
      this.issledovaniya = data.issledovaniya;
      this.loaded = true;
      this.select(-1);
      const tubesInGroups = {};

      for (const i of data.issledovaniya) {
        if (this.active === -1) {
          this.select(i.pk);
        }
        for (const t of i.tubes) {
          tubesInGroups[t.pk] = i.group;
        }
      }

      this.$root.$emit('laboratory:results:activate-pks',
        [data.direction.pk],
        _.uniq(_.flatten(data.issledovaniya.map(i => i.tubes.map(t => t.pk)))),
        tubesInGroups
      );
    })
  },
  computed: {
    fromRmis() {
      return this.loaded && this.direction && this.direction.imported_from_rmis;
    },
  },
  methods: {
    getStatusClass(i) {
      if (i.saved && !i.confirmed) {
        return 's';
      }

      if (i.confirmed) {
        return 'c';
      }

      if (!i.deff) {
        return 'n';
      }

      return 'o';
    },
    getStatus(i) {
      const status = this.getStatusClass(i);

      return {n: 'Не обработан', s: 'Обработан', c: 'Подтверждён', o: 'Отложен'}[status];
    },
    select(pk) {
      this.active = pk;
      this.$root.$emit('laboratory:results:open-form', pk);
    }
  },
}
</script>

<style scoped lang="scss">
.root {
  position: absolute;
  top: 0 !important;
  right: 0;
  left: 0;
  bottom: 0;
}

table {
  td, th {
    padding: 3px !important;
    font-size: 12px;
  }
}

.issledovaniya {
  margin: 0 3px;
  padding: 0;

  &-scroll-wrapper {
    overflow-x: visible;
    overflow-y: auto;
    position: absolute;
    top: 155px;
    left: 0;
    right: 0;
    bottom: 0;
  }

  li {
    list-style: none;
    cursor: pointer;
    margin: 3px 0;
    width: calc(100% - 3px);
    background-color: #f8fcfd;
    border-left-width: 3px;
    border-radius: 3px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
    transition: left .15s linear;
    position: relative;
    left: 3px;
    padding: 6px 6px 6px 9px;

    & small {
      color: rgba(0, 0, 0, .5);
      font-size: 8pt;
    }

    .hiddenlinks {
      opacity: 0;
      transition: .1s linear;
    }

    &:hover {
      background-color: #eef1f5;

      .hiddenlinks {
        opacity: 1;
      }

      small {
        color: #000
      }
    }

    &.active {
      background-color: #fff !important;
      color: #000 !important;
    }

    &:not(.active) {
      border: 1px solid #ECF0F1;
    }

    &:not(.issledovaniya-isnorm-maybe):not(.issledovaniya-isnorm-not_normal) {
      padding-right: 8px;
    }

    &.issledovaniya-isnorm-maybe, &.issledovaniya-isnorm-not_normal {
      border-right-width: 3px !important;
    }

    &.issledovaniya-isnorm-not_normal {
      border-right-color: #E68364 !important;
    }

    &.issledovaniya-isnorm-maybe {
      border-right-color: #F5D76E !important;
    }

    .status {
      float: right;
      display: inline-block;
      vertical-align: top;
      font-size: 11px;
      text-align: right;
      padding-bottom: 3px;
      position: absolute;
      right: 0;
      top: -3px;
    }

    .status-n {
      color: #CF3A24;
      font-weight: bold;
    }

    .status-s {
      color: #4B77BE;
    }

    .status-c {
      color: #049372
    }

    .status-o {
      color: #F7CA18;
    }
  }
}
</style>
