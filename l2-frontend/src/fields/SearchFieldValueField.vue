<template>
  <div>
    <div class="input-group">
      <span
        v-if="!readonly && (!once || (once && isStaticLink))"
        class="input-group-btn"
        style="vertical-align: top;"
      >
        <button
          v-tippy="{ placement: 'bottom', arrow: true }"
          class="btn btn-block"
          :class="{ btn_color: not_autoload_result }"
          :title="isStaticLink ? 'Загрузить данные' : 'Загрузить последний результат'"
          @click="loadLast"
        >
          <i class="fa fa-circle" />
        </button>
      </span>
      <textarea
        v-if="lines > 1"
        v-model="val"
        v-tippy="{ placement: 'bottom', arrow: true }"
        :readonly="readonly"
        :rows="lines"
        class="form-control"
        :placeholder="title"
        :title="title"
      />
      <input
        v-else
        v-model="val"
        v-tippy="{ placement: 'bottom', arrow: true }"
        :readonly="readonly"
        class="form-control"
        :placeholder="title"
        :title="title"
      >
    </div>
    <a
      v-if="direction"
      class="a-under"
      href="#"
      @click.prevent="print_results"
    >
      печать результатов направления {{ direction }}
    </a>
  </div>
</template>

<script lang="ts">
import researchesPoint from '@/api/researches-point';
import directionsPoint from '@/api/directions-point';

export default {
  name: 'SearchFieldValueField',
  model: {
    event: 'modified',
  },
  props: {
    readonly: {
      type: Boolean,
    },
    fieldPk: {
      type: String,
      required: false,
    },
    fieldPkInitial: {
      type: String,
      required: false,
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
      type: [String, Number],
      required: false,
    },
    once: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      val: this.value,
      title: '',
      direction: null,
      fpkInitial: this.fieldPkInitial,
    };
  },
  computed: {
    isStaticLink() {
      return this.fpk?.startsWith('%');
    },
    fpk() {
      return this.fpkInitial || this.fieldPk;
    },
  },
  watch: {
    val() {
      this.changeValue(this.val);
    },
    value() {
      this.val = this.value;
    },
  },
  mounted() {
    if (!this.raw) {
      researchesPoint.fieldTitle({ pk: this.fpk }).then(data => {
        const titles = new Set([data.research, data.group, data.field]);
        this.title = [...titles].filter(t => !!t).join(' – ');
        this.checkDirection();

        setTimeout(() => {
          if (!this.val && !this.not_autoload_result) {
            this.loadLast();
          }
        }, 200);
      });
    } else if (!this.val && !this.not_autoload_result) {
      this.loadLast();
    } else if (this.not_autoload_result && (!this.once || this.isStaticLink)) {
      this.val = '';
    } else if (!this.not_autoload_result && this.once && this.isStaticLink) {
      this.val = '';
      this.loadLast();
    }
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
      const { result } = await directionsPoint.lastFieldResult(this, ['clientPk', 'iss_pk'], { fieldPk: this.fpk });
      let logicalAnd = false;
      if (this.fpk.indexOf('&') > -1) {
        logicalAnd = true;
      }
      console.log(this.title);
      if (result) {
        this.direction = result.direction;
        if (this.raw || logicalAnd) {
          this.val = result.value;
        } else {
          this.val = `${result.value} (${result.date}, направление ${result.direction})`;
        }
      }
    },
    print_results() {
      this.$root.$emit('print:results', [this.direction]);
    },
  },
};
</script>

<style scoped land="scss">
.base input,
.base textarea {
  z-index: 1;
}

div.btn:hover {
  cursor: default;
}

.btn_color {
  color: #049372;
}

.btn-block {
  white-space: normal;
  text-align: left;
}

.input-group {
  width: 100%;
}
</style>
