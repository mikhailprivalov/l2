<template>
  <div>
    <div class="input-group base">
        <span class="input-group-btn" v-if="!readonly">
            <button class="btn" title="Загрузить последний результат"
                    @click="loadLast"
                    v-tippy="{ placement : 'bottom', arrow: true }">
                {{title}}&nbsp;&nbsp;<i class="fa fa-circle"></i>
            </button>
        </span>
      <span v-else class="input-group-addon">{{title}}</span>
      <input type="text" :readonly="readonly" v-model="val" class="form-control"/>
    </div>
    <a v-if="direction" href="#" class="a-under" @click.prevent="print_results">
      печать результатов направления {{direction}}
    </a>
  </div>
</template>

<script>
import researchesPoint from '../api/researches-point';
import directionsPoint from '../api/directions-point';

export default {
  name: 'SearchFractionValueField',
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
  watch: {
    val() {
      this.changeValue(this.val);
      this.checkDirection();
    },
  },
  model: {
    event: 'modified',
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
        window.errmessage(`Результат не найден (${this.title})!`);
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
