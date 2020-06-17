<template>
  <div>
    <div class="input-group" style="width: 100%;">
      <span class="input-group-btn" style="vertical-align: top;" v-if="!readonly">
        <button class="btn btn-block" style="white-space: normal;text-align: left;"
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
  import researches_point from '../api/researches-point'
  import directions_point from '../api/directions-point'

  export default {
    name: 'SearchFieldValueField',
    props: {
      readonly: {
        type: Boolean
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
      iss: {
        type: Number,
        required: false,
      },
      current_field_pk: {
        type: Number,
        required: true,
      }
    },
    data() {
      return {
        val: this.value,
        title: '',
        direction: null,
      }
    },
    mounted() {
      if (!this.raw) {

        researches_point.fieldTitle({pk: this.fieldPk}).then(data => {
          const titles = new Set([data.research, data.group, data.field])
          this.title = [...titles].filter(t => !!t).join(' – ')
          this.checkDirection()

          setTimeout(() => {
            if (!this.val) {
              this.loadLast()
            }
          }, 200)
        })
      }
      else if (!this.readonly){
        this.checkEmptyFieldResult()
        if (!this.val) {
          this.loadLast()
        }

      }
    },
    watch: {
      val() {
        this.changeValue(this.val)
      },
      value() {
        this.val = this.value;
      },
    },
    model: {
      event: 'modified'
    },
    methods: {
      checkDirection() {
        const res = /направление (\d+)\)$/gm.exec(this.val)
        this.direction = !res ? null : parseInt(res[1])
      },
      changeValue(newVal) {
        this.$emit('modified', newVal)
      },
      async checkEmptyFieldResult() {
        const prev_result = await directions_point.checkEmptyFieldResult(this, [
          'iss',
          'current_field_pk',
        ])
        if (prev_result && this.raw ) {
          this.val = prev_result.value;
        }
      },
      async loadLast() {
        this.direction = null;
        const {result} = await directions_point.lastFieldResult(this, [
          'fieldPk',
          'clientPk',
        ]);
        if (result) {
          this.direction = result.direction;
          if (this.raw) {
            this.val = result.value;
          } else {
            this.val = `${result.value} (${result.date}, направление ${result.direction})`;
          }
        } else {
          errmessage(`Результат не найден (${this.title})!`)
        }
      },
      print_results() {
        this.$root.$emit('print:results', [this.direction])
      },
    },
  }
</script>

<style scoped>
  .base input, .base textarea {
    z-index: 1;
  }

  div.btn:hover {
    cursor: default;
  }
</style>
