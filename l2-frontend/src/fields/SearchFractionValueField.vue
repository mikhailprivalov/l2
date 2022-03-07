<template>
  <div>
    <div class="input-group base">
      <span
        v-if="!readonly"
        class="input-group-btn"
      >
        <button
          v-tippy="{ placement : 'bottom', arrow: true }"
          class="btn"
          title="Загрузить последний результат"
          @click="loadLast"
        >
          {{ title }}&nbsp;&nbsp;<i class="fa fa-circle" />
        </button>
      </span>
      <span
        v-else
        class="input-group-addon"
      >{{ title }}</span>
      <input
        v-model="val"
        type="text"
        :readonly="readonly"
        class="form-control"
      >
    </div>
    <a
      v-if="direction"
      href="#"
      class="a-under"
      @click.prevent="print_results"
    >
      печать результатов направления {{ direction }}
    </a>
  </div>
</template>

<script lang="ts">
import researchesPoint from '../api/researches-point';
import directionsPoint from '../api/directions-point';

export default {
  name: 'SearchFractionValueField',
  model: {
    event: 'modified',
  },
  props: {
    readonly: {
      type: Boolean,
    },
    fractionPk: {
      type: String,
      required: true,
    },
    clientPk: {
      type: Number,
      required: true,
    },
    value: {
      required: false,
    },
  },
  data() {
    return {
      val: this.value,
      title: '',
      units: '',
      direction: null,
    };
  },
  watch: {
    val() {
      this.changeValue(this.val);
      this.checkDirection();
    },
  },
  mounted() {
    researchesPoint.fractionTitle({ pk: this.fractionPk }).then((data) => {
      const titles = new Set([data.research, data.fraction]);
      this.title = [...titles].join(' – ');
      this.units = data.units;
      this.checkDirection();

      setTimeout(() => {
        if (!this.val) {
          this.loadLast();
        }
      }, 200);
    });
  },
  methods: {
    checkDirection() {
      const res = /направление (\d+)\)$/gm.exec(this.val);
      this.direction = !res ? null : parseInt(res[1], 10);
    },
    changeValue(newVal) {
      this.$emit('modified', newVal);
    },
    async loadLast() {
      const { result } = await directionsPoint.lastFractionResult(this, [
        'fractionPk',
        'clientPk',
      ]);
      if (result) {
        this.val = `${result.value} (${result.date})`.replace('<br/>', '');
      } else {
        this.$root.$emit('msg', 'error', `Результат не найден (${this.title})!`);
      }
    },
    print_results() {
      this.$root.$emit('print:results', [this.direction]);
    },
  },
};
</script>

<style scoped>
  .base input {
    z-index: 1;
  }
</style>
