<template>
  <div v-frag>
    <div class="result-link"
         :class="!active && 'result-link-hidden'"
         @mouseover="show_results_debounce()"
         @mouseleave="hide_results"
    >
      <span class="a-under">{{ direction }}</span>

      <div class="result-dropdown">
        <table class="table table-bordered table-condensed" v-if="isLab">
          <colgroup>
            <col width='50'/>
            <col width='80'/>
            <col width='50'/>
            <col width='50'/>
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
            <tr v-for="f in row.fractions" :key="`${pk}_${f.title}_${f.value}`">
              <td>{{ row.title }}</td>
              <td>{{ f.title }}</td>
              <td>
                <span v-html="f.value"></span>
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

<script>
import api from '@/api';
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
    show_results_debounce: _.debounce(function (with_hide) {
      this.show_results(with_hide);
    }, 300),
    async show_results(with_hide) {
      if (with_hide) {
        return;
      }
      this.active = true;
      const result_data = await api('directions/result-patient-by-direction',
        this, ['isLab', 'isDocReferral', 'isParaclinic'], { dir: this.direction });
      this.result = result_data.results[0] || [];
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
    color: #3BAFDA;
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
  transition: all 0.3s cubic-bezier(.25, .8, .25, 1);
}
</style>
