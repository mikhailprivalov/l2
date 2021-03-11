<template>
  <fragment>
    <a href="#" class="a-under" @show="show_results" @click.prevent
       v-tippy="{
                html: `#result-${direction}`,
                reactive: false,
                interactive: true,
                // sticky: true,
                arrow: true,
                animation: 'fade',
                duration: 0,
                theme: 'light',
                placement: 'bottom',
                trigger: 'mouseenter click',
                zIndex: 5999,
                popperOptions: {
                  modifiers: {
                    preventOverflow: {
                      boundariesElement: 'window'
                    },
                    hide: {
                      enabled: false
                    }
                  }
                },
             }">
      {{ direction }}
    </a>

    <div :id="`result-${direction}`" style="display: none" v-tippy-html>
      <table class="table">
        <colgroup>
          <col width='50'/>
          <col width='80'/>
          <col width='300'/>
          <col/>
        </colgroup>
        <tbody>
        <tr>
          <td>Анализ</td>
          <td>Тест</td>
          <td>Значение</td>
          <td>Ед. изм</td>
        </tr>
        <tr v-for="row in result">
          <td></td>
          <td></td>
          <td></td>
          <td></td>
        </tr>
        </tbody>
      </table>
    </div>
  </fragment>
</template>

<script>
import api from '@/api'
import moment from "moment";

export default {
  name: "LaboratoryShowTippy",
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
    is_doc_refferal: {
      type: Boolean,
      required: false,
      default: false,
    },
    is_paraclinic: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
    data() {
      return {
        result: [],
      }
    },
    mounted() {
        // this.show_results();
    },
    methods: {
      async show_results() {
        const result_data = await api('directions/result-patient-by-direction',
          this, ['isLab', 'is_doc_refferal', 'is_paraclinic'], {'dir': this.direction});
        this.result = [...result_data.results]
        console.log(this.result)
      },
    }
}

</script>

<style scoped lang="scss">

i {
  vertical-align: middle;
  display: inline-block;
  margin-right: 3px;
}


.tp {
  text-align: left;
  padding: 1px;

  table {
    margin: 0;
  }

  max-height: 600px;
  overflow-y: auto;
}
</style>
