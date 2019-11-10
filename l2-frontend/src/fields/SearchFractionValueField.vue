<template>
  <div>
    <div class="input-group base">
        <span class="input-group-btn" v-if="!readonly">
            <button class="btn btn" title="Загрузить последний результат"
                    @click="loadLast"
                    v-tippy="{ placement : 'bottom', arrow: true }">
                {{title}}&nbsp;&nbsp;<i class="fa fa-circle"></i>
            </button>
        </span>
      <span v-else class="input-group-addon">{{title}}</span>
      <input type="text" :readonly="readonly" v-model="val" class="form-control"/>
    </div>
    <a v-if="direction" href="#" @click="print_results">печать результатов направления {{direction}}</a>
  </div>
</template>

<script>
    import researches_point from '../api/researches-point'
    import directions_point from '../api/directions-point'

    const regexDirection = /направление (\d+)\)$/gm

    export default {
        name: 'SearchFractionValueField',
        props: {
            readonly: {
                type: Boolean
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
                required: true,
            },
        },
        data() {
            return {
                val: this.value,
                title: '',
                units: '',
            }
        },
        mounted() {
            researches_point.fractionTitle({pk: this.fractionPk}).then(data => {
                const titles = new Set([data.research, data.fraction])
                this.title = [...titles].join(' – ')
                this.units = data.units
            })
        },
        watch: {
            val() {
                this.changeValue(this.val)
            },
        },
        model: {
            event: 'modified'
        },
        methods: {
            changeValue(newVal) {
                this.$emit('modified', newVal)
            },
            async loadLast() {
                const {result} = await directions_point.lastFractionResult(this, [
                    'fractionPk',
                    'clientPk',
                ])
                if (result) {
                    this.val = `${result.value}${this.units === '' ? '' : ' ' + this.units} (${result.date}, направление ${result.direction})`
                } else {
                    errmessage('Результат не найден!')
                }
            },
            print_results() {
                this.$root.$emit('print:results', [this.direction])
            },
        },
        computed: {
            direction() {
                const res = regexDirection.exec(this.val)
                if (!res) {
                    return null
                }
                return parseInt(res[1])
            },
        },
    }
</script>

<style scoped>
  .base input {
    z-index: 1;
  }
</style>
