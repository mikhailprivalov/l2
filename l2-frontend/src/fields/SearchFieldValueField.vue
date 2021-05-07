<template>
  <div>
    <div class="input-group" style="width: 100%;">
      <span class="input-group-btn" style="vertical-align: top;" v-if="!readonly">
        <button class="btn btn-block" :class="{btn_color: not_autoload_result}" style="white-space: normal;text-align: left;"
                title="Загрузить последний результат"
                @click="loadLast"
                v-tippy="{ placement : 'bottom', arrow: true }">
            <i class="fa fa-circle"/>
        </button>
      </span>
      <textarea :readonly="readonly" :rows="lines" class="form-control"
                :placeholder="title"
                v-tippy="{ placement : 'bottom', arrow: true }" :title="title" v-if="lines > 1" v-model="val"/>
      <input :readonly="readonly" class="form-control"
             :placeholder="title"
             v-tippy="{ placement : 'bottom', arrow: true }" :title="title" v-else v-model="val"/>
    </div>
    <a v-if="direction" class="a-under" href="#" @click.prevent="print_results">
      печать результатов направления {{direction}}
    </a>
  </div>
</template>

<script>
import researchesPoint from '../api/researches-point';
import directionsPoint from '../api/directions-point';

export default {
  name: 'SearchFieldValueField',
  props: {
    readonly: {
      type: Boolean,
    },
    fieldPk: {
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
    lines: {
      type: Number,
    },
    raw: {
      type: Boolean,
      required: false,
      default: false,
    },
    not_autoload_result: {
      type: Boolean,
      required: false,
      default: false,
    },
    iss_pk: {
      type: Number,
      required: false,
    },
  },
  data() {
    return {
      val: this.value,
      title: '',
      direction: null,
    };
  },
  mounted() {
    if (!this.raw) {
      researchesPoint.fieldTitle({ pk: this.fieldPk }).then((data) => {
        const titles = new Set([data.research, data.group, data.field]);
        this.title = [...titles].filter((t) => !!t).join(' – ');
        this.checkDirection();

        setTimeout(() => {
          if (!this.val && !this.not_autoload_result) {
            this.loadLast();
          }
        }, 200);
      });
    } else if (!this.val && !this.not_autoload_result) {
      this.loadLast();
    } else if (this.not_autoload_result) {
      this.val = '';
    }
  },
  watch: {
    val() {
      this.changeValue(this.val);
    },
    value() {
      this.val = this.value;
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
      this.direction = null;
      const { result } = await directionsPoint.lastFieldResult(this, [
        'fieldPk',
        'clientPk',
        'iss_pk',
      ]);
      let logicalAnd = false;
      if (this.fieldPk.indexOf('&') > -1) {
        logicalAnd = true;
      }
      if (result) {
        this.direction = result.direction;
        if (this.raw || logicalAnd) {
          this.val = result.value;
        } else {
          this.val = `${result.value} (${result.date}, направление ${result.direction})`;
        }
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
  .base input, .base textarea {
    z-index: 1;
  }

  div.btn:hover {
    cursor: default;
  }

  .btn_color {
    color: #049372;
  }
</style>
