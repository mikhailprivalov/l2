<template>
  <div v-frag>
    <div
      class="result-link"
      :class="!active && 'result-link-hidden'"
      @mouseover="show_results_debounce()"
      @mouseleave="hide_results"
    >
      <span class="a-under">{{ direction }}</span>

      <div class="result-dropdown">
        <table
          v-if="isLab"
          class="table table-bordered table-condensed"
        >
          <colgroup>
            <col width="50">
            <col width="80">
            <col width="50">
            <col width="50">
          </colgroup>
          <thead>
            <tr>
              <th>Анализ</th>
              <th>Тест</th>
              <th>Значение</th>
              <th>Ед. изм</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(row, pk) in result.researches">
              <tr
                v-for="f in row.fractions"
                :key="`${pk}_${f.title}_${f.value}`"
              >
                <td>{{ row.title }}</td>
                <td>{{ f.title }}</td>
                <td>
                  <span v-html="/*eslint-disable-line vue/no-v-html*/ f.value" />
                </td>
                <td>{{ f.units }}</td>
              </tr>
            </template>
          </tbody>
        </table>
        <div v-else>
          TODO: другие типы
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import _ from 'lodash';

export default {
  name: 'ResultDetails',
  props: {
    direction: {
      type: Number,
      required: true,
    },
    isLab: {
      type: Boolean,
      required: false,
      default: false,
    },
    isDocReferral: {
      type: Boolean,
      required: false,
      default: false,
    },
    isParaclinic: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      result: [],
      active: false,
    };
  },
  methods: {
    show_results_debounce: _.debounce(function (withHide) {
      this.show_results(withHide);
    }, 300),
    async show_results(withHide) {
      if (withHide) {
        return;
      }
      this.active = true;
      const resultData = await this.$api(
        'directions/result-patient-by-direction',
        this,
        ['isLab', 'isDocReferral', 'isParaclinic'],
        {
          dir: this.direction,
        },
      );
      this.result = resultData.results[0] || [];
    },
    hide_results() {
      this.show_results_debounce(true);
      this.active = false;
      this.result = [];
    },
  },
};
</script>

<style scoped lang="scss">
.result-link {
  display: inline-block;
  position: relative;

  .a-under {
    color: #3bafda;
    cursor: pointer;
  }

  &-hidden .result-dropdown {
    display: none;
  }
}

.result-dropdown {
  position: absolute;
  top: 100%;
  width: 480px;
  z-index: 6999;

  background: #fff;
  border-radius: 2px;
  display: block;
  padding: 5px;
  min-height: 10px;
  box-sizing: border-box;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.19), 0 6px 6px rgba(0, 0, 0, 0.23);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
</style>
