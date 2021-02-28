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
            {{direction.pk}}
          </a>
        </td>
        <th>Финанс.</th>
        <td>
          {{direction.fin_source}}
          <template v-if="fromRmis">внеш.орг</template>
        </td>
      </tr>
      <tr>
        <th>Пациент</th>
        <td colspan="3">
          {{patient.fio}}
        </td>
      </tr>
      <tr>
        <th>Пол</th>
        <td>{{patient.sex}}</td>
        <th>Возраст</th>
        <td>{{patient.age}}</td>
      </tr>
      <tr v-if="patient.history_num">
        <th>Карта</th>
        <td>{{patient.card}}</td>
        <th>Истор.</th>
        <td title="Номер истории">{{patient.history_num}}</td>
      </tr>
      <tr v-else>
        <th>Карта</th>
        <td colspan="3">{{patient.card}}</td>
      </tr>
      <tr title="Лечащий врач" v-if="!fromRmis">
        <th>Леч. врач</th>
        <td colspan="3">{{direction.directioner}}</td>
      </tr>
      <tr v-if="!fromRmis">
        <th>Отделение</th>
        <td colspan="3">{{direction.otd}}</td>
      </tr>
      <tr v-if="fromRmis">
        <th>Организация</th>
        <td colspan="3">{{direction.imported_org}}</td>
      </tr>
      </tbody>
    </table>
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
    };
  },
  mounted() {
    this.$root.$on('laboratory:results:show-direction', data => {
      this.direction = data.direction;
      this.patient = data.patient;
      this.issledovaniya = data.issledovaniya;
      this.loaded = true;
      const tubesInGroups = {};

      for (const i of data.issledovaniya) {
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
</style>
