<template>
  <div v-frag>
    <template v-if="!data.remove">
      <tr>
        <td>
          <button class="btn btn-blue-nb" v-if="data.isNew" @click="delete_row" v-tippy="{ placement : 'bottom'}"
                  title="Удалить назначение">
            <i class="fa fa-times"/>
          </button>
          {{ data.drug }}
        </td>
        <td class="cl-td">
          <select class="form-control nbr" :class="!isValidFormRelease && 'invalid'"
                  v-model.number="data.form_release" :readonly="confirmed">
            <option value="-1" v-if="data.form_release === -1" disabled>Не выбрано</option>
            <option :value="f.pk" v-for="f in params.formReleases" :key="f.pk">{{ f.title }}</option>
          </select>
        </td>
        <td class="cl-td">
          <select class="form-control nbr" :class="!isValidMethod && 'invalid'" v-model.number="data.method"
                  :readonly="confirmed">
            <option value="-1" v-if="data.method === -1" disabled>Не выбрано</option>
            <option :value="f.pk" v-for="f in params.methods" :key="f.pk">{{ f.title }}</option>
          </select>
        </td>
        <td class="cl-td">
          <input class="form-control" v-model.number="data.dosage" type="number" min="0" step="0.001"
                 :readonly="confirmed"/>
        </td>
        <td class="cl-td">
          <select class="form-control nbr" :class="!isValidUnits && 'invalid'" v-model="data.units"
                  :readonly="confirmed">
            <option :value="null" v-if="data.units === null" disabled>–</option>
            <option :value="u" v-for="u in params.units" :key="u">{{ u }}</option>
          </select>
        </td>
        <td class="cl-td">
          <Treeselect class="treeselect-noborder"
                      :multiple="true" :disable-branch-nodes="true" :options="timesToSelect"
                      placeholder="Режим приёма не выбран" v-model="data.timesSelected"
                      :searchable="false"
                      :append-to-body="true" :disabled="confirmed"/>
        </td>
        <td class="cl-td">
          <input class="form-control" v-model="data.dateStart" style="padding-left: 5px;padding-right: 0;" type="date"
                 :min="td" step="1" :readonly="confirmed"/>
        </td>
        <td class="cl-td">
          <input class="form-control" v-model.number="data.countDays" type="number" min="1" step="1"
                 :readonly="confirmed"/>
        </td>
        <td class="cl-td">
          <input class="form-control" v-model.number="data.step" type="number" min="1" max="5" step="1"
                 :readonly="confirmed"/>
        </td>
        <td>
          {{ dateEndVisible }}
        </td>
      </tr>
      <tr>
        <td colspan="10" class="cl-td">
          <input class="form-control" v-model="data.comment" :readonly="confirmed"
                 placeholder="Комментарий" maxlength="70"/>
        </td>
      </tr>
    </template>
  </div>
</template>

<script>
import Treeselect from '@riophae/vue-treeselect';
import '@riophae/vue-treeselect/dist/vue-treeselect.css';

import moment from 'moment';

export default {
  name: 'PharmacotherapyRow',
  components: { Treeselect },
  props: {
    data: {},
    params: {},
    confirmed: {},
  },
  computed: {
    isValidMethod() {
      if (!this.data.method) {
        return false;
      }

      return Number(this.data.method) > -1;
    },
    isValidFormRelease() {
      if (!this.data.form_release) {
        return false;
      }

      return Number(this.data.form_release) > -1;
    },
    isValidTimesSelected() {
      if (!this.data.timesSelected) {
        return false;
      }

      return this.data.timesSelected.length > 0;
    },
    isValidUnits() {
      return Boolean(this.data.units);
    },
    dateEnd() {
      return moment(this.data.dateStart).add(this.data.countDays, 'days').format('DD.MM.YYYY');
    },
    dateEndVisible() {
      if (this.data.step > 1) {
        const dates = [];
        for (let i = 0; i < this.data.countDays; i += this.data.step) {
          dates.push(
            moment(this.data.dateStart).add(i, 'days').format('DD.MM.YYYY'),
          );
        }
        return dates.join(' ');
      }
      return moment(this.data.dateStart).add(this.data.countDays - 1, 'days').format('DD.MM.YYYY');
    },
    timesToSelect() {
      return (this.params.times || []).map((t) => ({
        id: t,
        label: t,
      }));
    },
  },
  watch: {
    dateEnd: {
      immediate: true,
      handler() {
        this.data.dateEnd = this.dateEnd;
      },
    },
  },
  data() {
    return {
      td: moment().format('YYYY-MM-DD'),
    };
  },
  methods: {
    delete_row() {
      this.data.remove = true;
    },
  },
};
</script>

<style scoped lang="scss">
.invalid {
  border-color: #a94442;
  box-shadow: inset 0 0 5px rgba(#a94442, 0.93);
}
</style>
