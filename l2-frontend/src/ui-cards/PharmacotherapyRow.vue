<template>
  <div v-frag>
    <template v-if="!data.remove">
      <tr>
        <td>
          <button
            v-if="data.isNew"
            v-tippy="{ placement : 'bottom'}"
            class="btn btn-blue-nb"
            title="Удалить назначение"
            @click="delete_row"
          >
            <i class="fa fa-times" />
          </button>
          {{ data.drug }}
        </td>
        <td class="cl-td">
          <select
            v-model.number="/* eslint-disable-line vue/no-mutating-props */ data.form_release"
            class="form-control nbr"
            :class="!isValidFormRelease && 'invalid'"
            :readonly="confirmed"
          >
            <option
              v-if="data.form_release === -1"
              value="-1"
              disabled
            >
              Не выбрано
            </option>
            <option
              v-for="f in params.formReleases"
              :key="f.pk"
              :value="f.pk"
            >
              {{ f.title }}
            </option>
          </select>
        </td>
        <td class="cl-td">
          <select
            v-model.number="/* eslint-disable-line vue/no-mutating-props */ data.method"
            class="form-control nbr"
            :class="!isValidMethod && 'invalid'"
            :readonly="confirmed"
          >
            <option
              v-if="data.method === -1"
              value="-1"
              disabled
            >
              Не выбрано
            </option>
            <option
              v-for="f in params.methods"
              :key="f.pk"
              :value="f.pk"
            >
              {{ f.title }}
            </option>
          </select>
        </td>
        <td class="cl-td">
          <input
            v-model.number="/* eslint-disable-line vue/no-mutating-props */ data.dosage"
            class="form-control"
            type="number"
            min="0"
            step="0.001"
            :readonly="confirmed"
          >
        </td>
        <td class="cl-td">
          <select
            v-model="/* eslint-disable-line vue/no-mutating-props */ data.units"
            class="form-control nbr"
            :class="!isValidUnits && 'invalid'"
            :readonly="confirmed"
          >
            <option
              v-if="data.units === null"
              :value="null"
              disabled
            >
              –
            </option>
            <option
              v-for="u in params.units"
              :key="u"
              :value="u"
            >
              {{ u }}
            </option>
          </select>
        </td>
        <td class="cl-td">
          <Treeselect
            v-model="/* eslint-disable-line vue/no-mutating-props */ data.timesSelected"
            class="treeselect-noborder"
            :multiple="true"
            :disable-branch-nodes="true"
            :options="timesToSelect"
            placeholder="Режим приёма не выбран"
            :searchable="false"
            :append-to-body="true"
            :disabled="confirmed"
          />
        </td>
        <td class="cl-td">
          <input
            v-model="/* eslint-disable-line vue/no-mutating-props */ data.dateStart"
            class="form-control"
            style="padding-left: 5px;padding-right: 0;"
            type="date"
            :min="td"
            step="1"
            :readonly="confirmed"
          >
        </td>
        <td class="cl-td">
          <input
            v-model.number="/* eslint-disable-line vue/no-mutating-props */ data.countDays"
            class="form-control"
            type="number"
            min="1"
            step="1"
            :readonly="confirmed"
          >
        </td>
        <td class="cl-td">
          <input
            v-model.number="/* eslint-disable-line vue/no-mutating-props */ data.step"
            class="form-control"
            type="number"
            min="1"
            max="5"
            step="1"
            :readonly="confirmed"
          >
        </td>
        <td>
          {{ dateEndVisible }}
        </td>
      </tr>
      <tr>
        <td
          colspan="10"
          class="cl-td"
        >
          <input
            v-model="/* eslint-disable-line vue/no-mutating-props */ data.comment"
            class="form-control"
            :readonly="confirmed"
            placeholder="Комментарий"
            maxlength="70"
          >
        </td>
      </tr>
    </template>
  </div>
</template>

<script lang="ts">
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
  data() {
    return {
      td: moment().format('YYYY-MM-DD'),
    };
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
        // eslint-disable-next-line vue/no-mutating-props
        this.data.dateEnd = this.dateEnd;
      },
    },
  },
  methods: {
    delete_row() {
      // eslint-disable-next-line vue/no-mutating-props
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
